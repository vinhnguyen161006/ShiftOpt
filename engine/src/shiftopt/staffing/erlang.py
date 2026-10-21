from collections.abc import Sequence


def required_staff_erlang(
    arrival_rates: Sequence[float], mean_service_hours: float, target_service_level: float
) -> tuple[int, ...]:
    """TODO: smallest agents per hour meeting the service level with Erlang A (Erlang C when no
    abandonment); square-root staffing N = R + beta * sqrt(R) is the fast fallback."""
    raise NotImplementedError
