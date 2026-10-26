import statistics
from collections.abc import Callable
from dataclasses import dataclass

from shiftopt.domain import Assignment, Instance, ShiftType, Solution
from shiftopt.time_grid import HOURS_PER_WEEK, shift_hours

WEEKEND_DAYS = (5, 6)


@dataclass(frozen=True)
class Kpi:
    coverage_ratio: float
    understaffed_hours: int
    overstaffed_hours: int
    schedule_efficiency: float
    labor_cost: int
    night_premium_cost: int
    night_shift_stddev: float
    weekend_shift_stddev: float


def staff_by_hour(instance: Instance, solution: Solution) -> tuple[int, ...]:
    """Head count on duty for each of the 168 hours of the week. A shift counts for every hour
    it covers, so overnight hours land on the following day. Unknown shift names raise KeyError;
    run validate first to reject them."""
    staff = [0] * HOURS_PER_WEEK
    for assignment in solution.assignments:
        shift = instance.shift_by_name(assignment.shift_name)
        for hour in shift_hours(assignment.day, shift.start_hour, shift.length):
            staff[hour] += 1
    return tuple(staff)


def labor_cost(instance: Instance, solution: Solution) -> int:
    """Total pay in hundredths of the wage unit, night premium included (Article 98 clause 2).
    Unknown employee or shift ids raise KeyError; run validate first."""
    wages = _wages(instance)
    return sum(
        wages[assignment.employee_id]
        * instance.shift_by_name(assignment.shift_name).cost_per_wage_unit(instance.rules)
        for assignment in solution.assignments
    )


def night_premium_cost(instance: Instance, solution: Solution) -> int:
    """Night premium part of labor_cost: wage * night_premium_percent * night hours."""
    wages = _wages(instance)
    return sum(
        wages[assignment.employee_id]
        * instance.rules.night_premium_percent
        * instance.shift_by_name(assignment.shift_name).night_hours(instance.rules)
        for assignment in solution.assignments
    )


def labor_cost_share(cost: int, revenue: float) -> float:
    """Labor cost as a fraction of assumed revenue. The revenue figure is a team assumption
    supplied by the caller, in the same units as cost."""
    if revenue <= 0:
        raise ValueError("revenue must be positive")
    return cost / revenue


def compute_kpi(instance: Instance, solution: Solution) -> Kpi:
    """coverage_ratio = sum(min(staff, demand)) / sum(demand);
    understaffed = sum(max(0, demand - staff)); overstaffed = sum(max(0, staff - demand));
    efficiency = sum(demand) / sum(staff). A ratio with a zero denominator is 1.0.
    Fairness is the population standard deviation of night and weekend shift counts over every
    employee in the instance, including employees with no such shift. Unknown ids raise KeyError;
    run validate first."""
    demand = instance.demand
    staff = staff_by_hour(instance, solution)
    night_counts = _count_per_employee(
        instance, solution, lambda _, shift: shift.is_night_shift(instance.rules)
    )
    weekend_counts = _count_per_employee(
        instance, solution, lambda assignment, _: assignment.day in WEEKEND_DAYS
    )
    return Kpi(
        coverage_ratio=_ratio(
            sum(min(on_duty, required) for on_duty, required in zip(staff, demand, strict=True)),
            sum(demand),
        ),
        understaffed_hours=sum(
            max(0, required - on_duty) for on_duty, required in zip(staff, demand, strict=True)
        ),
        overstaffed_hours=sum(
            max(0, on_duty - required) for on_duty, required in zip(staff, demand, strict=True)
        ),
        schedule_efficiency=_ratio(sum(demand), sum(staff)),
        labor_cost=labor_cost(instance, solution),
        night_premium_cost=night_premium_cost(instance, solution),
        night_shift_stddev=_spread(night_counts),
        weekend_shift_stddev=_spread(weekend_counts),
    )


def _wages(instance: Instance) -> dict[str, int]:
    return {employee.id: employee.hourly_wage for employee in instance.employees}


def _count_per_employee(
    instance: Instance,
    solution: Solution,
    counts_toward: Callable[[Assignment, ShiftType], bool],
) -> list[int]:
    counts = {employee.id: 0 for employee in instance.employees}
    for assignment in solution.assignments:
        shift = instance.shift_by_name(assignment.shift_name)
        if counts_toward(assignment, shift):
            counts[assignment.employee_id] += 1
    return list(counts.values())


def _spread(counts: list[int]) -> float:
    return statistics.pstdev(counts) if counts else 0.0


def _ratio(numerator: float, denominator: float) -> float:
    return 1.0 if denominator == 0 else numerator / denominator
