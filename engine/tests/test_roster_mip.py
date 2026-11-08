from collections.abc import Callable
from dataclasses import replace

from shiftopt.domain import Assignment, Employee, Instance, RepairSpec, ShiftType, Solution
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.models.roster_mip import solve_roster_mip
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
InstanceFactory = Callable[..., Instance]
AFTERNOON = ShiftType("afternoon", 14)
MORNING = ShiftType("morning", 6)


def test_mip_and_cpsat_agree_on_shortfall_and_cost() -> None:
    day_shift = tuple(1 if 8 <= hour < 16 else 0 for hour in range(HOURS_PER_WEEK))
    instance = Instance(
        demand=day_shift,
        employees=tuple(Employee(f"e{index}", 100) for index in range(3)),
        shift_types=(ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16)),
    )

    mip = solve_roster_mip(instance, PARAMS)
    cpsat = solve_roster(instance, PARAMS)

    assert mip.result.status is SolveStatus.OPTIMAL
    assert cpsat.result.status is SolveStatus.OPTIMAL
    assert mip.phases[0].objective == cpsat.phases[0].objective
    assert mip.phases[1].objective == cpsat.phases[1].objective


def test_mip_roster_has_no_hard_violations(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)

    outcome = solve_roster_mip(instance, PARAMS)

    assert outcome.solution.assignments
    assert validate(instance, outcome.solution) == []


def test_mip_never_rosters_afternoon_then_next_morning() -> None:
    instance = Instance(
        demand=tuple(
            1 if hour in (hour_of_week(0, 15), hour_of_week(1, 7)) else 0
            for hour in range(HOURS_PER_WEEK)
        ),
        employees=(Employee("solo", 100),),
        shift_types=(AFTERNOON, MORNING),
    )

    outcome = solve_roster_mip(instance, PARAMS)

    days = {(item.day, item.shift_name) for item in outcome.solution.assignments}
    assert not ({(0, "afternoon"), (1, "morning")} <= days)
    assert validate(instance, outcome.solution) == []


def test_mip_repair_with_all_days_locked_keeps_baseline(
    build_instance: InstanceFactory,
) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)
    baseline = solve_roster_mip(instance, PARAMS).solution

    outcome = solve_roster_mip(instance, PARAMS, repair=RepairSpec(baseline, from_day=7))

    assert outcome.solution == baseline
    assert outcome.changes == 0


def test_mip_repair_counts_changes_as_symmetric_difference(
    build_instance: InstanceFactory,
) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)
    baseline = solve_roster_mip(instance, PARAMS).solution
    first = instance.employees[0]
    absent_day = min(item.day for item in baseline.assignments if item.employee_id == "e0")
    employees = (replace(first, unavailable_days=frozenset({absent_day})), *instance.employees[1:])
    absent = replace(instance, employees=employees)

    outcome = solve_roster_mip(absent, PARAMS, repair=RepairSpec(baseline, from_day=absent_day))

    before = {(a.employee_id, a.day, a.shift_name) for a in baseline.assignments}
    after = {(a.employee_id, a.day, a.shift_name) for a in outcome.solution.assignments}
    assert outcome.changes == len(before ^ after)
    assert validate(absent, outcome.solution) == []


def test_mip_pinned_shift_is_rostered(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)
    pinned = Assignment("e1", 5, "day", 3)

    outcome = solve_roster_mip(instance, PARAMS, repair=RepairSpec(Solution(()), pinned=(pinned,)))

    assert pinned in outcome.solution.assignments
    assert validate(instance, outcome.solution) == []


def test_mip_is_reproducible(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)

    first = solve_roster_mip(instance, PARAMS)
    second = solve_roster_mip(instance, PARAMS)

    assert first.result.objective == second.result.objective
    assert first.solution == second.solution


def test_relaxed_model_bounds_integer_objective(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)

    integer = solve_roster_mip(instance, PARAMS)
    relaxed = solve_roster_mip(instance, PARAMS, relax=True)

    assert relaxed.phases[1].objective is not None
    assert integer.phases[1].objective is not None
    assert relaxed.phases[1].objective <= integer.phases[1].objective + 1e-6
