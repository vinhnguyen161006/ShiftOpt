from dataclasses import replace

import pytest

from shiftopt.domain import Assignment, Employee, Instance, RepairSpec, ShiftType, Solution
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
QUICK = SolveParams(time_limit_seconds=20, num_workers=1, random_seed=0)
SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def keys(solution: Solution) -> set[tuple[str, int, str]]:
    return {(item.employee_id, item.day, item.shift_name) for item in solution.assignments}


def before(solution: Solution, day: int) -> set[Assignment]:
    return {item for item in solution.assignments if item.day < day}


def crew_instance(demand_per_hour: int, count: int = 8) -> Instance:
    return Instance(
        demand=(demand_per_hour,) * HOURS_PER_WEEK,
        employees=tuple(Employee(f"e{index}", 100) for index in range(count)),
        shift_types=SHIFTS,
    )


@pytest.fixture(scope="module")
def roster() -> tuple[Instance, Solution]:
    instance = crew_instance(demand_per_hour=1)
    outcome = solve_roster(instance, PARAMS)
    assert validate(instance, outcome.solution) == []
    return instance, outcome.solution


def test_fully_locked_repair_keeps_roster(roster: tuple[Instance, Solution]) -> None:
    instance, baseline = roster
    outcome = solve_roster(instance, QUICK, repair=RepairSpec(baseline, from_day=7))
    assert outcome.solution == baseline
    assert outcome.changes == 0


def test_absence_keeps_locked_days_and_counts_changes(
    roster: tuple[Instance, Solution],
) -> None:
    instance, baseline = roster
    day = min(
        item.day for item in baseline.assignments if item.employee_id == "e0" and item.day >= 2
    )
    first = instance.employees[0]
    employees = (replace(first, unavailable_days=frozenset({day})), *instance.employees[1:])
    absent = replace(instance, employees=employees)

    outcome = solve_roster(absent, QUICK, repair=RepairSpec(baseline, from_day=2))

    assert validate(absent, outcome.solution) == []
    assert before(outcome.solution, 2) == before(baseline, 2)
    assert all(item.day != day for item in outcome.solution.assignments if item.employee_id == "e0")
    assert outcome.changes == len(keys(baseline) ^ keys(outcome.solution))
    assert outcome.changes is not None
    assert outcome.changes >= 1


def test_pinned_shift_is_rostered() -> None:
    instance = crew_instance(demand_per_hour=1)
    pinned = Assignment("e1", 5, "day")

    outcome = solve_roster(instance, QUICK, repair=RepairSpec(Solution(()), pinned=(pinned,)))

    assert pinned in outcome.solution.assignments
    assert validate(instance, outcome.solution) == []


def test_demand_increase_keeps_locked_days(roster: tuple[Instance, Solution]) -> None:
    _, baseline = roster
    harder = crew_instance(demand_per_hour=2)

    outcome = solve_roster(harder, QUICK, repair=RepairSpec(baseline, from_day=3))

    assert before(outcome.solution, 3) == before(baseline, 3)
    assert validate(harder, outcome.solution) == []


def test_repair_is_reproducible() -> None:
    instance = Instance(
        demand=tuple(1 if hour == hour_of_week(0, 9) else 0 for hour in range(HOURS_PER_WEEK)),
        employees=(Employee("e0", 100), Employee("e1", 100)),
        shift_types=SHIFTS,
    )
    baseline = solve_roster(instance, PARAMS).solution
    spec = RepairSpec(baseline, from_day=2)
    first = solve_roster(instance, PARAMS, repair=spec)
    second = solve_roster(instance, PARAMS, repair=spec)
    assert first.result.objective == second.result.objective
    assert first.changes == second.changes


def test_repair_rejects_symmetry_breaking(roster: tuple[Instance, Solution]) -> None:
    instance, baseline = roster
    with pytest.raises(ValueError, match="cannot be combined"):
        solve_roster(instance, QUICK, symmetry_breaking=True, repair=RepairSpec(baseline))


def test_repair_rejects_decomposition(roster: tuple[Instance, Solution]) -> None:
    instance, baseline = roster
    with pytest.raises(ValueError, match="cannot be combined"):
        solve_roster(instance, QUICK, decompose=True, repair=RepairSpec(baseline))


def test_pinned_shift_on_unavailable_day_is_rejected() -> None:
    instance = crew_instance(demand_per_hour=1, count=2)
    first = instance.employees[0]
    employees = (replace(first, unavailable_days=frozenset({4})), *instance.employees[1:])
    blocked = replace(instance, employees=employees)
    spec = RepairSpec(Solution(()), pinned=(Assignment("e0", 4, "day"),))
    with pytest.raises(ValueError, match="cannot work"):
        solve_roster(blocked, QUICK, repair=spec)


def test_repair_spec_rejects_bad_from_day() -> None:
    with pytest.raises(ValueError, match="from_day must be in"):
        RepairSpec(Solution(()), from_day=8)


def test_locked_employee_must_exist() -> None:
    instance = crew_instance(demand_per_hour=1, count=2)
    spec = RepairSpec(Solution((Assignment("ghost", 0, "day"),)), from_day=1)
    with pytest.raises(ValueError, match="unknown employee or shift"):
        solve_roster(instance, QUICK, repair=spec)
