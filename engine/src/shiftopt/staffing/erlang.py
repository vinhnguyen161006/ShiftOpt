"""Call-centre staffing from hourly arrival rates (calls per hour) and handle time in seconds.

Implemented: Erlang C (M/M/n, no abandonment), Erlang A (M/M/n+M, exponential patience) and
square-root staffing N = R + beta * sqrt(R). Erlang C ignores abandonment and therefore tends to
overstaff; Erlang A uses the virtual waiting time, so the same load needs no more agents.
"""

import math
from collections.abc import Sequence

from shiftopt.staffing.linear import tolerant_ceil
from shiftopt.time_grid import HOURS_PER_WEEK

SECONDS_PER_HOUR = 3600
DEFAULT_SERVICE_LEVEL = 0.8
DEFAULT_ANSWER_SECONDS = 20
ERLANG_TAIL_TOLERANCE = 1e-12
POISSON_TAIL_SIGMAS = 12
POISSON_TAIL_MARGIN = 30
MAX_PATIENCE_SECONDS = 3600


def erlang_c_wait_probability(agents: int, offered_load: float) -> float:
    """Probability that a call waits, Erlang C. Uses the Erlang B recursion
    B(n) = a * B(n-1) / (n + a * B(n-1)), which avoids factorial overflow, then
    C = n * B / (n - a * (1 - B)). Requires agents > offered_load for a stable queue."""
    if agents <= offered_load:
        raise ValueError("agents must exceed the offered load")
    blocking = 1.0
    for servers in range(1, agents + 1):
        blocking = offered_load * blocking / (servers + offered_load * blocking)
    return agents * blocking / (agents - offered_load * (1 - blocking))


def erlang_c_service_level(
    agents: int, offered_load: float, handle_seconds: float, answer_seconds: float
) -> float:
    """Fraction of calls answered within answer_seconds:
    1 - C * exp(-(n - a) * answer_seconds / handle_seconds)."""
    wait_probability = erlang_c_wait_probability(agents, offered_load)
    return 1 - wait_probability * math.exp(
        -(agents - offered_load) * answer_seconds / handle_seconds
    )


def erlang_a_queue_probabilities(
    agents: int, offered_load: float, handle_seconds: float, patience_seconds: float
) -> tuple[float, ...]:
    """Stationary distribution of the M/M/n+M queue. Entry k is the probability of k calls in the
    system, with service rate 1 / handle_seconds and abandonment rate 1 / patience_seconds per
    waiting call. Birth-death recursion in log space; the list ends once the tail is below
    ERLANG_TAIL_TOLERANCE of the peak, so it is finite even when the queue would be unstable."""
    _check_queue_inputs(agents, offered_load, handle_seconds, patience_seconds)
    service_rate = 1 / handle_seconds
    abandon_rate = 1 / patience_seconds
    log_arrival = math.log(offered_load * service_rate)
    log_weights = [0.0]
    peak = 0.0
    while True:
        state = len(log_weights)
        death_rate = min(state, agents) * service_rate + max(state - agents, 0) * abandon_rate
        log_weights.append(log_weights[-1] + log_arrival - math.log(death_rate))
        peak = max(peak, log_weights[-1])
        if state > agents and log_weights[-1] < peak + math.log(ERLANG_TAIL_TOLERANCE):
            break
    weights = [math.exp(log_weight - peak) for log_weight in log_weights]
    total = sum(weights)
    return tuple(weight / total for weight in weights)


def _virtual_wait_within(
    queue_size: int,
    agents: int,
    handle_seconds: float,
    patience_seconds: float,
    answer_seconds: float,
) -> list[float]:
    """P(virtual waiting time <= answer_seconds) for an arrival that finds j queued calls, for
    j in [0, queue_size). The virtual wait ignores the arrival's own abandonment; calls ahead
    still leave by service or abandonment. Uniformization: a discrete chain with the same moves
    at uniform rate, mixed by Poisson weights, so every term is non-negative."""
    if answer_seconds == 0 or queue_size == 0:
        return [0.0] * queue_size
    service_rate = 1 / handle_seconds
    abandon_rate = 1 / patience_seconds
    uniform_rate = agents * service_rate + max(queue_size - 1, 0) * abandon_rate
    move_down = [
        (agents * service_rate + ahead * abandon_rate) / uniform_rate for ahead in range(queue_size)
    ]
    mean_steps = uniform_rate * answer_seconds
    log_mean = math.log(mean_steps)
    within = [0.0] * queue_size
    served_by_step = [0.0] * queue_size
    cumulative = 0.0
    max_steps = math.ceil(
        mean_steps + POISSON_TAIL_SIGMAS * math.sqrt(mean_steps) + POISSON_TAIL_MARGIN
    )
    for steps in range(max_steps + 1):
        weight = math.exp(-mean_steps + steps * log_mean - math.lgamma(steps + 1))
        within = [
            total + weight * value for total, value in zip(within, served_by_step, strict=True)
        ]
        cumulative += weight
        if cumulative >= 1 - ERLANG_TAIL_TOLERANCE:
            break
        served_by_step = [
            (1 - move_down[ahead]) * served_by_step[ahead]
            + move_down[ahead] * (served_by_step[ahead - 1] if ahead > 0 else 1.0)
            for ahead in range(queue_size)
        ]
    return within


def erlang_a_service_level(
    agents: int,
    offered_load: float,
    handle_seconds: float,
    patience_seconds: float,
    answer_seconds: float,
) -> float:
    """Fraction of calls whose virtual waiting time is at most answer_seconds, under Erlang A
    with exponential patience (Garnett, Mandelbaum and Reiman 2002). Calls that find an idle agent
    count as answered at once; the rest use the queue distribution and the virtual wait CDF."""
    if answer_seconds < 0:
        raise ValueError("answer_seconds must be non-negative")
    probabilities = erlang_a_queue_probabilities(
        agents, offered_load, handle_seconds, patience_seconds
    )
    queued = probabilities[agents:]
    within = _virtual_wait_within(
        len(queued), agents, handle_seconds, patience_seconds, answer_seconds
    )
    return sum(probabilities[:agents]) + sum(
        probability * chance for probability, chance in zip(queued, within, strict=True)
    )


def _offered_loads(arrival_rates: Sequence[float], handle_seconds: float) -> list[float]:
    if len(arrival_rates) != HOURS_PER_WEEK:
        raise ValueError(f"arrival_rates must have {HOURS_PER_WEEK} entries")
    if any(not math.isfinite(rate) or rate < 0 for rate in arrival_rates):
        raise ValueError("arrival rates must be finite and non-negative")
    if handle_seconds <= 0:
        raise ValueError("handle_seconds must be positive")
    return [rate * handle_seconds / SECONDS_PER_HOUR for rate in arrival_rates]


def _check_queue_inputs(
    agents: int, offered_load: float, handle_seconds: float, patience_seconds: float
) -> None:
    if agents < 1:
        raise ValueError("agents must be at least 1")
    if offered_load <= 0:
        raise ValueError("offered_load must be positive")
    if handle_seconds <= 0:
        raise ValueError("handle_seconds must be positive")
    if patience_seconds <= 0:
        raise ValueError("patience_seconds must be positive")


def _check_service_target(
    target_service_level: float, answer_seconds: float, min_staff: int
) -> None:
    if not 0 < target_service_level < 1:
        raise ValueError("target_service_level must be in (0, 1)")
    if answer_seconds < 0:
        raise ValueError("answer_seconds must be non-negative")
    if min_staff < 0:
        raise ValueError("min_staff must be non-negative")


def _erlang_c_agents(
    offered_load: float, handle_seconds: float, target_service_level: float, answer_seconds: float
) -> int:
    agents = math.floor(offered_load) + 1
    while (
        erlang_c_service_level(agents, offered_load, handle_seconds, answer_seconds)
        < target_service_level
    ):
        agents += 1
    return agents


def _erlang_a_agents(
    offered_load: float,
    handle_seconds: float,
    patience_seconds: float,
    target_service_level: float,
    answer_seconds: float,
) -> int:
    def meets_target(agents: int) -> bool:
        return (
            erlang_a_service_level(
                agents, offered_load, handle_seconds, patience_seconds, answer_seconds
            )
            >= target_service_level
        )

    low = 1
    high = _erlang_c_agents(offered_load, handle_seconds, target_service_level, answer_seconds)
    while low < high:
        middle = (low + high) // 2
        if meets_target(middle):
            high = middle
        else:
            low = middle + 1
    return high


def required_staff_erlang_c(
    arrival_rates: Sequence[float],
    handle_seconds: float,
    target_service_level: float,
    answer_seconds: float,
    min_staff: int,
) -> tuple[int, ...]:
    """Smallest agents per hour whose Erlang C service level reaches the target
    (default 80 percent answered within 20 seconds), never below min_staff."""
    loads = _offered_loads(arrival_rates, handle_seconds)
    _check_service_target(target_service_level, answer_seconds, min_staff)
    return tuple(
        max(
            min_staff,
            _erlang_c_agents(load, handle_seconds, target_service_level, answer_seconds)
            if load > 0
            else 0,
        )
        for load in loads
    )


def required_staff_erlang_a(
    arrival_rates: Sequence[float],
    handle_seconds: float,
    patience_seconds: float,
    target_service_level: float,
    answer_seconds: float,
    min_staff: int,
) -> tuple[int, ...]:
    """Smallest agents per hour whose Erlang A service level (virtual wait) reaches the target,
    never below min_staff. The search is bounded above by the Erlang C staffing, since abandonment
    never needs more agents. patience_seconds has no default: it is a team assumption, and is
    capped at MAX_PATIENCE_SECONDS because the queue grows with patience."""
    loads = _offered_loads(arrival_rates, handle_seconds)
    _check_service_target(target_service_level, answer_seconds, min_staff)
    if not 0 < patience_seconds <= MAX_PATIENCE_SECONDS:
        raise ValueError(f"patience_seconds must be in (0, {MAX_PATIENCE_SECONDS}]")
    return tuple(
        max(
            min_staff,
            _erlang_a_agents(
                load, handle_seconds, patience_seconds, target_service_level, answer_seconds
            )
            if load > 0
            else 0,
        )
        for load in loads
    )


def required_staff_square_root(
    arrival_rates: Sequence[float], handle_seconds: float, beta: float, min_staff: int
) -> tuple[int, ...]:
    """Square-root staffing per hour: max(min_staff, ceil(R + beta * sqrt(R))), R the offered
    load in Erlangs. Fast approximation; beta sets the quality of service."""
    loads = _offered_loads(arrival_rates, handle_seconds)
    if beta < 0:
        raise ValueError("beta must be non-negative")
    if min_staff < 0:
        raise ValueError("min_staff must be non-negative")
    return tuple(max(min_staff, tolerant_ceil(load + beta * math.sqrt(load))) for load in loads)
