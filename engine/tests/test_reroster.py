from dataclasses import replace

import pytest

from shiftopt.domain import Employee, Instance, ShiftType, Solution
from shiftopt.models.roster_cpsat import Reroster, solve_roster
from shiftopt.schedule_diff import diff_solutions
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def build(demand_at: dict[tuple[int, int], int], employees: tuple[Employee, ...]) -> Instance:
    demand = [0] * 168
    for (day, hour), value in demand_at.items():
        demand[day * 24 + hour] = value
    return Instance(tuple(demand), employees, SHIFTS)


def absent_on(instance: Instance, employee_id: str, day: int) -> Instance:
    employees = tuple(
        replace(employee, unavailable_days=employee.unavailable_days | {day})
        if employee.id == employee_id
        else employee
        for employee in instance.employees
    )
    return replace(instance, employees=employees)


def trio() -> Instance:
    employees = (Employee("e0", 100), Employee("e1", 100), Employee("e2", 100))
    return build({(2, 9): 1, (4, 9): 1, (0, 17): 1}, employees)


def assignee_on(solution: Solution, day: int) -> str:
    return next(a.employee_id for a in solution.assignments if a.day == day)


def test_absent_employee_is_not_rostered_on_absent_day() -> None:
    instance = trio()
    previous = solve_roster(instance, PARAMS).solution
    absent_id = assignee_on(previous, 2)
    new_instance = absent_on(instance, absent_id, 2)

    outcome = solve_roster(new_instance, PARAMS, reroster=Reroster(previous))

    assert validate(new_instance, outcome.solution) == []
    assert not any(a.employee_id == absent_id and a.day == 2 for a in outcome.solution.assignments)
    assert outcome.understaffed_hours == 0


def test_one_absent_day_costs_exactly_one_drop_and_one_add() -> None:
    instance = trio()
    previous = solve_roster(instance, PARAMS).solution
    absent_id = assignee_on(previous, 2)
    new_instance = absent_on(instance, absent_id, 2)

    outcome = solve_roster(new_instance, PARAMS, reroster=Reroster(previous))

    diff = diff_solutions(previous, outcome.solution)
    assert outcome.changes == 2
    assert len(diff.added) + len(diff.removed) == outcome.changes


def test_locked_days_keep_previous_assignments() -> None:
    instance = trio()
    previous = solve_roster(instance, PARAMS).solution
    absent_id = assignee_on(previous, 2)
    new_instance = absent_on(instance, absent_id, 2)
    locked = frozenset({0, 1})

    outcome = solve_roster(new_instance, PARAMS, reroster=Reroster(previous, locked))

    def early(solution: Solution) -> set[tuple[str, int, str]]:
        return {
            (a.employee_id, a.day, a.shift_name) for a in solution.assignments if a.day in locked
        }

    assert early(outcome.solution) == early(previous)
    assert validate(new_instance, outcome.solution) == []


def test_locked_assignment_on_absent_day_is_rejected() -> None:
    instance = trio()
    previous = solve_roster(instance, PARAMS).solution
    absent_id = assignee_on(previous, 2)
    new_instance = absent_on(instance, absent_id, 2)

    with pytest.raises(ValueError, match="locked assignment"):
        solve_roster(new_instance, PARAMS, reroster=Reroster(previous, frozenset({2})))


def test_coverage_stays_soft_when_no_one_is_left() -> None:
    employees = (Employee("e0", 100), Employee("e1", 100))
    instance = build({(2, 9): 2}, employees)
    previous = solve_roster(instance, PARAMS).solution
    new_instance = absent_on(instance, "e0", 2)

    outcome = solve_roster(new_instance, PARAMS, reroster=Reroster(previous))

    assert outcome.result.status is not SolveStatus.INFEASIBLE
    assert outcome.understaffed_hours == 1
    assert validate(new_instance, outcome.solution) == []


def test_without_reroster_changes_is_none() -> None:
    outcome = solve_roster(trio(), PARAMS)

    assert outcome.changes is None
