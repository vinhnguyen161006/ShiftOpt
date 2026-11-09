from dataclasses import dataclass
from enum import StrEnum

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import PERCENT_BASE, Employee, Instance, ShiftType
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY, is_night_hour


class WarningKind(StrEnum):
    NO_AVAILABLE_DAYS = "no_available_days"
    CAPACITY_BELOW_DEMAND = "capacity_below_demand"
    NO_NIGHT_SHIFT = "no_night_shift"
    MIN_HOURS_UNREACHABLE = "min_hours_unreachable"
    BUDGET_BELOW_DEMAND = "budget_below_demand"


@dataclass(frozen=True)
class PreSolveWarning:
    kind: WarningKind
    detail: str
    employee_id: str | None = None


def diagnose(instance: Instance) -> tuple[PreSolveWarning, ...]:
    """Necessary conditions that no roster can meet, checked before solving. Each warning proves
    that some coverage hours must fall short, so none is a false alarm. Order is deterministic:
    employees in instance order, then capacity, then night demand.

    no_available_days: an employee has every day of the week unavailable.
    capacity_below_demand: the paid hours of any roster are at most the sum over employees of
    min(weekly cap, workable days * longest allowed shift), where workable days are the available
    days capped by the cyclic consecutive-day rule (floor(7 * K / (K + 1))). Breaks only reduce
    coverage further, so when this bound is below the total demand in person-hours, shortfall is
    certain. Shifts longer than max_daily_hours are excluded, as the roster model excludes them.
    no_night_shift: night demand exists but no allowed shift covers any night hour (Article 106).
    min_hours_unreachable: an employee's contract minimum exceeds the most hours they can work.
    The minimum is soft, so the roster stays feasible and the shortfall is reported.
    budget_below_demand: every covered person-hour costs at least the lowest wage times
    PERCENT_BASE, so a weekly budget below demand times that rate leaves some hour uncovered.
    """
    rules = instance.rules
    allowed = _allowed_shifts(instance)
    warnings = [
        PreSolveWarning(
            WarningKind.NO_AVAILABLE_DAYS,
            f"employee {employee.id} has no available day",
            employee.id,
        )
        for employee in instance.employees
        if len(employee.unavailable_days) >= DAYS_PER_WEEK
    ]
    capacity = sum(_capacity(employee, allowed, rules) for employee in instance.employees)
    demand = sum(instance.demand)
    if capacity < demand:
        warnings.append(
            PreSolveWarning(
                WarningKind.CAPACITY_BELOW_DEMAND,
                f"paid hours of at most {capacity} cannot meet demand of {demand} person-hours",
            )
        )
    if _night_demand(instance) > 0 and not any(shift.night_hours(rules) > 0 for shift in allowed):
        warnings.append(
            PreSolveWarning(
                WarningKind.NO_NIGHT_SHIFT,
                "night demand exists but no allowed shift covers any night hour",
            )
        )
    warnings.extend(
        PreSolveWarning(
            WarningKind.MIN_HOURS_UNREACHABLE,
            f"employee {employee.id} has a minimum of {employee.min_weekly_hours} hours but can "
            f"work at most {_capacity(employee, allowed, rules)}",
            employee.id,
        )
        for employee in instance.employees
        if employee.min_weekly_hours is not None
        and employee.min_weekly_hours > _capacity(employee, allowed, rules)
    )
    floor = _cheapest_coverage(instance)
    if instance.weekly_budget is not None and instance.weekly_budget < floor:
        warnings.append(
            PreSolveWarning(
                WarningKind.BUDGET_BELOW_DEMAND,
                f"weekly budget {instance.weekly_budget} is below the cheapest possible cost "
                f"{floor} of covering demand",
            )
        )
    return tuple(warnings)


def _cheapest_coverage(instance: Instance) -> int:
    if not instance.employees:
        return 0
    cheapest = min(employee.hourly_wage for employee in instance.employees)
    return sum(instance.demand) * cheapest * PERCENT_BASE


def _allowed_shifts(instance: Instance) -> tuple[ShiftType, ...]:
    return tuple(
        shift for shift in instance.shift_types if shift.length <= instance.rules.max_daily_hours
    )


def _capacity(employee: Employee, allowed: tuple[ShiftType, ...], rules: LaborRules) -> int:
    if not allowed:
        return 0
    cyclic_days = DAYS_PER_WEEK * rules.max_consecutive_days // (rules.max_consecutive_days + 1)
    workable = min(DAYS_PER_WEEK - len(employee.unavailable_days), cyclic_days)
    longest = max(shift.length for shift in allowed)
    return min(employee.weekly_cap(rules), workable * longest)


def _night_demand(instance: Instance) -> int:
    rules = instance.rules
    return sum(
        load
        for hour, load in enumerate(instance.demand)
        if is_night_hour(hour % HOURS_PER_DAY, rules.night_start, rules.night_end)
    )
