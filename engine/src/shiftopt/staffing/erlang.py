"""Call-centre staffing from hourly arrival rates (calls per hour) and handle time in seconds.

Implemented: Erlang C (M/M/n, no abandonment) and square-root staffing N = R + beta * sqrt(R).
Erlang C ignores abandonment and therefore tends to overstaff; Erlang A is deferred to task 6.2.
"""

import math
from collections.abc import Sequence

from shiftopt.staffing.linear import tolerant_ceil
from shiftopt.time_grid import HOURS_PER_WEEK

SECONDS_PER_HOUR = 3600
DEFAULT_SERVICE_LEVEL = 0.8
DEFAULT_ANSWER_SECONDS = 20


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


def _offered_loads(arrival_rates: Sequence[float], handle_seconds: float) -> list[float]:
    if len(arrival_rates) != HOURS_PER_WEEK:
        raise ValueError(f"arrival_rates must have {HOURS_PER_WEEK} entries")
    if any(not math.isfinite(rate) or rate < 0 for rate in arrival_rates):
        raise ValueError("arrival rates must be finite and non-negative")
    if handle_seconds <= 0:
        raise ValueError("handle_seconds must be positive")
    return [rate * handle_seconds / SECONDS_PER_HOUR for rate in arrival_rates]


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
    if not 0 < target_service_level < 1:
        raise ValueError("target_service_level must be in (0, 1)")
    if answer_seconds < 0:
        raise ValueError("answer_seconds must be non-negative")
    if min_staff < 0:
        raise ValueError("min_staff must be non-negative")
    return tuple(
        max(
            min_staff,
            _erlang_c_agents(load, handle_seconds, target_service_level, answer_seconds)
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
