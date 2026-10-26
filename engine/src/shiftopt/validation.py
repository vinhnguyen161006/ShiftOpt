from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY, HOURS_PER_WEEK


class ViolationKind(StrEnum):
    UNKNOWN_EMPLOYEE = "unknown_employee"
    UNKNOWN_SHIFT = "unknown_shift"
    MULTIPLE_SHIFTS_PER_DAY = "multiple_shifts_per_day"
    DAILY_HOURS = "daily_hours"
    WEEKLY_HOURS = "weekly_hours"
    REST_BETWEEN_SHIFTS = "rest_between_shifts"
    CONSECUTIVE_DAYS = "consecutive_days"
    WEEKLY_REST = "weekly_rest"
    MISSING_BREAK = "missing_break"
    BREAK_OUTSIDE_WINDOW = "break_outside_window"
    UNAVAILABLE_DAY = "unavailable_day"


LEGAL_BASIS: dict[ViolationKind, str] = {
    ViolationKind.UNKNOWN_EMPLOYEE: "Input data",
    ViolationKind.UNKNOWN_SHIFT: "Input data",
    ViolationKind.MULTIPLE_SHIFTS_PER_DAY: "Roster rule",
    ViolationKind.DAILY_HOURS: "Article 105",
    ViolationKind.WEEKLY_HOURS: "Article 105",
    ViolationKind.REST_BETWEEN_SHIFTS: "Article 110",
    ViolationKind.CONSECUTIVE_DAYS: "Roster rule",
    ViolationKind.WEEKLY_REST: "Article 111",
    ViolationKind.MISSING_BREAK: "Article 109",
    ViolationKind.BREAK_OUTSIDE_WINDOW: "Article 109",
    ViolationKind.UNAVAILABLE_DAY: "Employee request",
}


@dataclass(frozen=True)
class Violation:
    kind: ViolationKind
    employee_id: str
    detail: str
    day: int | None = None


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    day: int
    shift: ShiftType


def validate(instance: Instance, solution: Solution) -> list[Violation]:
    """Re-check every hard constraint from first principles on the absolute hour axis.

    Does not import models or solvers. The week is cyclic, so rest gaps and day runs wrap from
    Sunday to Monday. Checks: one shift per day, daily and weekly hours (Article 105), rest of at
    least 12 hours between consecutive shifts (Article 110), maximum consecutive working days, and
    a longest rest gap of at least 24 hours (Article 111), which a calendar day off alone does not
    guarantee for overnight shifts. Each shift that needs a rest break (Article 109) must carry a
    break offset inside its break window, and an employee is never rostered on an unavailable day.
    """
    shifts = {shift.name: shift for shift in instance.shift_types}
    employee_ids = {employee.id for employee in instance.employees}
    violations: list[Violation] = []
    rostered: dict[str, list[Assignment]] = {employee_id: [] for employee_id in employee_ids}
    for assignment in solution.assignments:
        if assignment.employee_id not in employee_ids:
            violations.append(
                Violation(
                    ViolationKind.UNKNOWN_EMPLOYEE,
                    assignment.employee_id,
                    "employee is not in the instance",
                    assignment.day,
                )
            )
        elif assignment.shift_name not in shifts:
            violations.append(
                Violation(
                    ViolationKind.UNKNOWN_SHIFT,
                    assignment.employee_id,
                    f"shift {assignment.shift_name} is not in the instance",
                    assignment.day,
                )
            )
        else:
            rostered[assignment.employee_id].append(assignment)
    for employee in instance.employees:
        violations.extend(_check_employee(employee, rostered[employee.id], shifts, instance.rules))
    return violations


def _check_employee(
    employee: Employee,
    assignments: list[Assignment],
    shifts: dict[str, ShiftType],
    rules: LaborRules,
) -> list[Violation]:
    employee_id = employee.id
    violations = _multiple_shifts_per_day(employee_id, assignments)
    violations.extend(_request_violations(employee, assignments))
    violations.extend(_break_violations(employee_id, assignments, shifts, rules))
    spans = sorted(
        (_span(assignment, shifts[assignment.shift_name]) for assignment in assignments),
        key=lambda span: span.start,
    )
    violations.extend(_hour_violations(employee_id, spans, rules))
    if not spans:
        return violations
    gaps = _rest_gaps(spans)
    violations.extend(_rest_violations(employee_id, gaps, rules))
    violations.extend(_weekly_rest_violations(employee_id, gaps, rules))
    violations.extend(_consecutive_violations(employee_id, spans, rules))
    return violations


def _request_violations(employee: Employee, assignments: list[Assignment]) -> list[Violation]:
    return [
        Violation(
            ViolationKind.UNAVAILABLE_DAY,
            employee.id,
            f"rostered on day {assignment.day}, which the employee cannot work",
            assignment.day,
        )
        for assignment in assignments
        if assignment.day in employee.unavailable_days
    ]


def _break_violations(
    employee_id: str,
    assignments: list[Assignment],
    shifts: dict[str, ShiftType],
    rules: LaborRules,
) -> list[Violation]:
    violations: list[Violation] = []
    for assignment in assignments:
        shift = shifts[assignment.shift_name]
        window = shift.break_window(rules)
        if assignment.break_offset is None:
            if window:
                violations.append(
                    Violation(
                        ViolationKind.MISSING_BREAK,
                        employee_id,
                        f"shift {shift.name} has no break, allowed offsets {window[0]} to "
                        f"{window[-1]}",
                        assignment.day,
                    )
                )
        elif assignment.break_offset not in window:
            violations.append(
                Violation(
                    ViolationKind.BREAK_OUTSIDE_WINDOW,
                    employee_id,
                    f"break at offset {assignment.break_offset} is not allowed for shift "
                    f"{shift.name}",
                    assignment.day,
                )
            )
    return violations


def _span(assignment: Assignment, shift: ShiftType) -> _Span:
    start = assignment.day * HOURS_PER_DAY + shift.start_hour
    return _Span(start=start, end=start + shift.length, day=assignment.day, shift=shift)


def _multiple_shifts_per_day(employee_id: str, assignments: list[Assignment]) -> list[Violation]:
    counts = Counter(assignment.day for assignment in assignments)
    return [
        Violation(
            ViolationKind.MULTIPLE_SHIFTS_PER_DAY,
            employee_id,
            f"{count} shifts on day {day}",
            day,
        )
        for day, count in sorted(counts.items())
        if count > 1
    ]


def _hour_violations(employee_id: str, spans: list[_Span], rules: LaborRules) -> list[Violation]:
    violations = [
        Violation(
            ViolationKind.DAILY_HOURS,
            employee_id,
            f"{span.shift.length} hours on day {span.day}, maximum {rules.max_daily_hours}",
            span.day,
        )
        for span in spans
        if span.shift.length > rules.max_daily_hours
    ]
    weekly = sum(span.shift.length for span in spans)
    if weekly > rules.max_weekly_hours:
        violations.append(
            Violation(
                ViolationKind.WEEKLY_HOURS,
                employee_id,
                f"{weekly} hours in the week, maximum {rules.max_weekly_hours}",
            )
        )
    return violations


def _rest_gaps(spans: list[_Span]) -> list[tuple[int, int]]:
    gaps: list[tuple[int, int]] = []
    for index, span in enumerate(spans):
        next_index = (index + 1) % len(spans)
        next_span = spans[next_index]
        next_start = next_span.start + (HOURS_PER_WEEK if next_index == 0 else 0)
        gaps.append((next_start - span.end, next_span.day))
    return gaps


def _rest_violations(
    employee_id: str, gaps: list[tuple[int, int]], rules: LaborRules
) -> list[Violation]:
    return [
        Violation(
            ViolationKind.REST_BETWEEN_SHIFTS,
            employee_id,
            f"{gap} hours of rest before the shift on day {day}, "
            f"minimum {rules.min_rest_between_shifts}",
            day,
        )
        for gap, day in gaps
        if gap < rules.min_rest_between_shifts
    ]


def _weekly_rest_violations(
    employee_id: str, gaps: list[tuple[int, int]], rules: LaborRules
) -> list[Violation]:
    longest = max(gap for gap, _ in gaps)
    if longest >= rules.weekly_rest_hours:
        return []
    return [
        Violation(
            ViolationKind.WEEKLY_REST,
            employee_id,
            f"longest rest is {longest} hours, minimum {rules.weekly_rest_hours}",
        )
    ]


def _consecutive_violations(
    employee_id: str, spans: list[_Span], rules: LaborRules
) -> list[Violation]:
    run = _longest_cyclic_run({span.day for span in spans})
    if run <= rules.max_consecutive_days:
        return []
    return [
        Violation(
            ViolationKind.CONSECUTIVE_DAYS,
            employee_id,
            f"{run} working days in a row, maximum {rules.max_consecutive_days}",
        )
    ]


def _longest_cyclic_run(days: set[int]) -> int:
    if len(days) == DAYS_PER_WEEK:
        return DAYS_PER_WEEK
    longest = 0
    for start in days:
        run = 0
        while (start + run) % DAYS_PER_WEEK in days:
            run += 1
        longest = max(longest, run)
    return longest
