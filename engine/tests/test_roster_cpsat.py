import random
from collections.abc import Callable

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.roster_cpsat import solve_roster, symmetry_pairs
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
THREE_SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def instance_with(
    demand_at: dict[tuple[int, int], int],
    employees: tuple[Employee, ...],
    shifts: tuple[ShiftType, ...] = THREE_SHIFTS,
) -> Instance:
    demand = [0] * HOURS_PER_WEEK
    for (day, hour), value in demand_at.items():
        demand[hour_of_week(day, hour)] = value
    return Instance(demand=tuple(demand), employees=employees, shift_types=shifts)


def crew(count: int, wage: int = 100) -> tuple[Employee, ...]:
    return tuple(Employee(f"e{index}", wage) for index in range(count))


def test_enough_staff_gives_full_coverage_without_violations(
    build_instance: Callable[..., Instance],
) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=8)
    outcome = solve_roster(instance, PARAMS)
    assert outcome.phases[0].status is SolveStatus.OPTIMAL
    assert outcome.understaffed_hours == 0
    assert outcome.result.status in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    assert validate(instance, outcome.solution) == []


def test_too_few_staff_stays_feasible_and_reports_shortfall(
    build_instance: Callable[..., Instance],
) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)
    outcome = solve_roster(instance, PARAMS)
    assert outcome.result.status is not SolveStatus.INFEASIBLE
    assert outcome.understaffed_hours is not None
    assert outcome.understaffed_hours >= 42
    assert validate(instance, outcome.solution) == []


def test_same_seed_gives_same_objective() -> None:
    instance = instance_with({(0, 9): 1}, crew(2))
    first = solve_roster(instance, PARAMS)
    second = solve_roster(instance, PARAMS)
    assert first.result.status is SolveStatus.OPTIMAL
    assert first.result.objective == second.result.objective


def test_afternoon_then_next_morning_is_never_rostered() -> None:
    instance = instance_with(
        {(0, 15): 1, (1, 7): 1},
        crew(1),
        shifts=(
            ShiftType("afternoon", 14),
            ShiftType("morning", 6),
        ),
    )
    outcome = solve_roster(instance, PARAMS)
    assert validate(instance, outcome.solution) == []
    assert outcome.understaffed_hours == 1


def test_shortfall_priority_beats_cost() -> None:
    cheap, expensive = Employee("cheap", 100), Employee("expensive", 1000)
    instance = instance_with({(0, 9): 2}, (cheap, expensive))
    outcome = solve_roster(instance, PARAMS)
    assert outcome.understaffed_hours == 0
    assert {a.employee_id for a in outcome.solution.assignments if a.day == 0} == {
        "cheap",
        "expensive",
    }


def test_unavailable_day_is_never_rostered() -> None:
    blocked = Employee("blocked", 100, unavailable_days=frozenset({0}))
    free = Employee("free", 100)
    instance = instance_with({(0, 9): 1}, (blocked, free))
    outcome = solve_roster(instance, PARAMS)
    assert outcome.understaffed_hours == 0
    assert all(a.employee_id != "blocked" for a in outcome.solution.assignments)
    assert validate(instance, outcome.solution) == []


def test_preferred_day_off_is_respected_when_free() -> None:
    wish = Employee("wish", 100, preferred_days_off=frozenset({0}))
    other = Employee("other", 100)
    instance = instance_with({(0, 9): 1}, (wish, other))
    outcome = solve_roster(instance, PARAMS)
    assert outcome.preference_misses == 0
    assert all(a.employee_id != "wish" for a in outcome.solution.assignments)


def test_random_small_rosters_pass_the_validator() -> None:
    for seed in range(2):
        rng = random.Random(seed)
        demand_at = {(day, hour): rng.randint(0, 1) for day in range(5) for hour in range(8, 17)}
        instance = instance_with(demand_at, crew(4))
        outcome = solve_roster(
            instance, SolveParams(time_limit_seconds=15, num_workers=1, random_seed=seed)
        )
        assert outcome.result.status is not SolveStatus.UNKNOWN
        assert validate(instance, outcome.solution) == []


def test_rules_are_read_from_instance_not_constants() -> None:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=crew(1),
        shift_types=(ShiftType("day", 8),),
        rules=LaborRules(max_weekly_hours=40),
    )
    outcome = solve_roster(instance, PARAMS)
    assert validate(instance, outcome.solution) == []


def test_symmetry_breaking_keeps_objective() -> None:
    instance = instance_with({(0, 9): 2}, crew(3))
    short = SolveParams(time_limit_seconds=30, num_workers=1, random_seed=0)
    with_symmetry = solve_roster(instance, short, symmetry_breaking=True)
    without_symmetry = solve_roster(instance, short, symmetry_breaking=False)
    assert with_symmetry.result.status is SolveStatus.OPTIMAL
    assert without_symmetry.result.status is SolveStatus.OPTIMAL
    assert with_symmetry.result.objective == without_symmetry.result.objective
    assert validate(instance, with_symmetry.solution) == []


def test_symmetry_skips_employees_with_requests() -> None:
    employees = (
        Employee("a", 100),
        Employee("b", 100, preferred_days_off=frozenset({3})),
        Employee("c", 100),
        Employee("d", 200),
        Employee("e", 100),
    )
    assert symmetry_pairs(employees) == [(0, 2), (2, 4)]


def test_decomposed_roster_is_flagged_approximate() -> None:
    instance = instance_with({(0, 9): 1, (1, 9): 1}, crew(2))
    outcome = solve_roster(
        instance, SolveParams(time_limit_seconds=30, num_workers=1, random_seed=0), decompose=True
    )
    assert outcome.approximate is True
    assert outcome.result.status is not SolveStatus.OPTIMAL
    assert validate(instance, outcome.solution) == []
