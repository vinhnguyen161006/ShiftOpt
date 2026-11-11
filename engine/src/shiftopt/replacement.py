from dataclasses import dataclass

from shiftopt.domain import Assignment, Instance, Solution
from shiftopt.validation import validate


@dataclass(frozen=True)
class Candidate:
    employee_id: str
    shift_name: str
    extra_cost: int
    weekly_hours: int
    prefers_off: bool


def suggest_replacements(
    instance: Instance, solution: Solution, employee_id: str, day: int, limit: int
) -> tuple[Candidate, ...]:
    """Employees who can take the shift that employee_id holds on day, same shift type, ranked
    by (prefers the day off, extra wage cost, weekly hours, id). A candidate is kept only when the
    roster with the swap passes every hard constraint, checked by validate. The absent employee's
    shift is removed first; removing shifts never breaks a constraint, so only the candidate's own
    rest, hours and days can cause a rejection."""
    absent = [
        item for item in solution.assignments if item.employee_id == employee_id and item.day == day
    ]
    if not absent:
        raise ValueError(f"employee {employee_id} has no shift on day {day}")
    target = absent[0]
    shift = instance.shift_by_name(target.shift_name)
    remaining = tuple(item for item in solution.assignments if item not in absent)
    hours = {employee.id: 0 for employee in instance.employees}
    lengths = {existing.name: existing.length for existing in instance.shift_types}
    for item in remaining:
        hours[item.employee_id] += lengths[item.shift_name]
    busy = {item.employee_id for item in remaining if item.day == day}
    candidates: list[Candidate] = []
    for employee in instance.employees:
        if employee.id == employee_id or employee.id in busy or day in employee.unavailable_days:
            continue
        swap = Assignment(employee.id, day, shift.name)
        if validate(instance, Solution((*remaining, swap))):
            continue
        candidates.append(
            Candidate(
                employee_id=employee.id,
                shift_name=shift.name,
                extra_cost=employee.hourly_wage * shift.cost_per_wage_unit(instance.rules),
                weekly_hours=hours[employee.id] + shift.length,
                prefers_off=day in employee.preferred_days_off,
            )
        )
    candidates.sort(
        key=lambda item: (item.prefers_off, item.extra_cost, item.weekly_hours, item.employee_id)
    )
    return tuple(candidates[:limit])
