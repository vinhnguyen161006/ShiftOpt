from dataclasses import dataclass

from shiftopt.domain import Instance, Solution


@dataclass(frozen=True)
class Kpi:
    coverage_ratio: float
    understaffed_hours: int
    overstaffed_hours: int
    schedule_efficiency: float
    labor_cost: int


def staff_by_hour(instance: Instance, solution: Solution) -> tuple[int, ...]:
    """TODO: head count on duty for each of the 168 hours of the week."""
    raise NotImplementedError


def labor_cost(instance: Instance, solution: Solution) -> int:
    """TODO: total pay in hundredths of the wage unit, night premium included."""
    raise NotImplementedError


def compute_kpi(instance: Instance, solution: Solution) -> Kpi:
    """TODO: coverage_ratio = sum(min(staff, demand)) / sum(demand);
    understaffed = sum(max(0, demand - staff)); overstaffed = sum(max(0, staff - demand));
    efficiency = sum(demand) / sum(staff). A ratio with a zero denominator is 1.0."""
    raise NotImplementedError
