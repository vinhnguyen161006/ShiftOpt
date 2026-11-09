from collections import Counter
from dataclasses import dataclass

from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.kpi import labor_cost, staff_by_hour
from shiftopt.time_grid import (
    DAYS_PER_WEEK,
    HOURS_PER_DAY,
    HOURS_PER_WEEK,
    covers_hour,
    hour_of_week,
)
from shiftopt.validation import ViolationKind, validate


@dataclass(frozen=True)
class HourExplanation:
    """One understaffed hour of the week. blocked counts, per violation kind, how many employees
    could not take a shift covering the hour because of that kind. free_employees lists the people
    who could take such a shift without breaking any rule or the budget. uncoverable is True when
    no allowed shift type works that hour at all, so no roster could staff it."""

    hour: int
    shortfall: int
    blocked: tuple[tuple[ViolationKind, int], ...]
    free_employees: tuple[str, ...]
    uncoverable: bool = False


def explain_shortfall(instance: Instance, solution: Solution) -> tuple[HourExplanation, ...]:
    """For every understaffed hour, find what stops each employee from covering it. An employee
    who already works at the hour is skipped. For the others, every allowed shift that covers the
    hour on the day it starts or the day before is tried as one extra assignment, checked on that
    employee alone with validate, plus the weekly budget. If some candidate is clean the employee
    is free; otherwise the candidate with the fewest new violation kinds supplies the reasons.

    When the shortfall tier of the solve is OPTIMAL no employee can be free, because a legal
    extra shift would lower the shortfall. A FEASIBLE solve may leave free employees, so the
    caller must say the solver had not found them within the time limit. An employee on their
    rest break counts as not working, so a second shift that day is reported as a violation.
    Does not import models or solvers. Unknown shift or employee ids raise KeyError; run validate
    first."""
    staff = staff_by_hour(instance, solution)
    spent = labor_cost(instance, solution)
    shifts = {shift.name: shift for shift in instance.shift_types}
    allowed = tuple(
        shift for shift in instance.shift_types if shift.length <= instance.rules.max_daily_hours
    )
    rows: dict[str, list[Assignment]] = {employee.id: [] for employee in instance.employees}
    for assignment in solution.assignments:
        rows[assignment.employee_id].append(assignment)
    explanations = []
    for hour in range(HOURS_PER_WEEK):
        short = instance.demand[hour] - staff[hour]
        if short <= 0:
            continue
        options = _covering_options(instance, hour, allowed)
        if not options:
            explanations.append(HourExplanation(hour, short, (), (), uncoverable=True))
            continue
        blocked: Counter[ViolationKind] = Counter()
        free: list[str] = []
        for employee in instance.employees:
            current = rows[employee.id]
            if any(hour in _worked_hours(item, shifts[item.shift_name]) for item in current):
                continue
            kinds = _blocking_kinds(instance, employee, current, options, shifts, spent)
            if kinds:
                blocked.update(kinds)
            else:
                free.append(employee.id)
        explanations.append(
            HourExplanation(
                hour=hour,
                shortfall=short,
                blocked=tuple(sorted(blocked.items(), key=lambda item: (-item[1], item[0].value))),
                free_employees=tuple(free),
            )
        )
    return tuple(explanations)


def _blocking_kinds(
    instance: Instance,
    employee: Employee,
    current: list[Assignment],
    options: list[tuple[int, ShiftType, int | None]],
    shifts: dict[str, ShiftType],
    spent: int,
) -> frozenset[ViolationKind]:
    alone = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(employee,),
        shift_types=instance.shift_types,
        rules=instance.rules,
    )
    existing = {item.kind for item in validate(alone, Solution(tuple(current)))}
    best: frozenset[ViolationKind] | None = None
    for day, shift, offset in options:
        candidate = Assignment(employee.id, day, shift.name, offset)
        kinds = {item.kind for item in validate(alone, Solution((*current, candidate)))} - existing
        cost = employee.hourly_wage * shifts[shift.name].cost_per_wage_unit(instance.rules)
        if instance.weekly_budget is not None and spent + cost > instance.weekly_budget:
            kinds.add(ViolationKind.OVER_BUDGET)
        if not kinds:
            return frozenset()
        if best is None or len(kinds) < len(best):
            best = frozenset(kinds)
    return best if best is not None else frozenset()


def _covering_options(
    instance: Instance, hour: int, allowed: tuple[ShiftType, ...]
) -> list[tuple[int, ShiftType, int | None]]:
    first_day = hour // HOURS_PER_DAY
    options = []
    for day in (first_day, (first_day - 1) % DAYS_PER_WEEK):
        for shift in allowed:
            start = day * HOURS_PER_DAY + shift.start_hour
            if covers_hour(hour, start, shift.length, HOURS_PER_WEEK):
                options.append((day, shift, _break_offset(instance, day, shift, hour)))
    return options


def _break_offset(instance: Instance, day: int, shift: ShiftType, hour: int) -> int | None:
    window = shift.break_window(instance.rules)
    if not window:
        return None
    return next(
        (offset for offset in window if hour_of_week(day, shift.start_hour + offset) != hour),
        window[0],
    )


def _worked_hours(assignment: Assignment, shift: ShiftType) -> set[int]:
    worked = {
        hour_of_week(assignment.day, shift.start_hour + offset) for offset in range(shift.length)
    }
    if assignment.break_offset is not None:
        worked.discard(hour_of_week(assignment.day, shift.start_hour + assignment.break_offset))
    return worked
