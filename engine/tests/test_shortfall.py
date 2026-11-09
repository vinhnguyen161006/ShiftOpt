import ast
from pathlib import Path

from shiftopt import shortfall
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.shortfall import HourExplanation, explain_shortfall
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import ViolationKind

DAY = ShiftType("day", 8)
EVENING = ShiftType("evening", 16)
NIGHT = ShiftType("night", 0)
SHIFTS = (NIGHT, DAY, EVENING)
PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
DAY_HOURS = tuple(hour_of_week(0, hour) for hour in range(8, 16))


def demand_on_day_zero(level: int) -> tuple[int, ...]:
    demand = [0] * HOURS_PER_WEEK
    for hour in DAY_HOURS:
        demand[hour] = level
    return tuple(demand)


def instance_of(
    employees: tuple[Employee, ...], level: int = 2, budget: int | None = None
) -> Instance:
    return Instance(
        demand=demand_on_day_zero(level),
        employees=employees,
        shift_types=SHIFTS,
        weekly_budget=budget,
    )


def first_hour(explanations: tuple[HourExplanation, ...]) -> HourExplanation:
    assert explanations
    return explanations[0]


def reasons(explanation: HourExplanation) -> dict[ViolationKind, int]:
    return dict(explanation.blocked)


def test_no_explanation_when_demand_is_met() -> None:
    instance = instance_of((Employee("e0", 100), Employee("e1", 100)), level=1)
    roster = Solution((Assignment("e0", 0, "day", 4), Assignment("e1", 0, "day", 5)))

    assert explain_shortfall(instance, roster) == ()


def test_unavailable_day_is_named_as_the_reason() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100, unavailable_days=frozenset({0})))
    roster = Solution((Assignment("e0", 0, "day", 4),))

    explanations = explain_shortfall(instance_of(crew), roster)

    assert reasons(first_hour(explanations)) == {ViolationKind.UNAVAILABLE_DAY: 1}
    assert all(item.free_employees == () for item in explanations)


def test_an_idle_legal_employee_is_reported_as_free() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100))
    roster = Solution((Assignment("e0", 0, "day", 4),))

    explanations = explain_shortfall(instance_of(crew), roster)

    assert all(item.free_employees == ("e1",) for item in explanations)
    assert first_hour(explanations).blocked == ()


def test_weekly_hours_is_named_when_the_employee_is_full() -> None:
    full = tuple(Assignment("e1", day, "day", 4) for day in range(1, 7))
    crew = (Employee("e0", 100), Employee("e1", 100))
    roster = Solution((Assignment("e0", 0, "day", 4), *full))

    explanations = explain_shortfall(instance_of(crew), roster)

    assert ViolationKind.WEEKLY_HOURS in reasons(first_hour(explanations))


def test_rest_between_shifts_is_named_for_a_late_shift_before_the_morning() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100))
    roster = Solution((Assignment("e0", 0, "day", 4), Assignment("e1", 6, "evening", 4)))

    explanations = explain_shortfall(instance_of(crew), roster)

    assert ViolationKind.REST_BETWEEN_SHIFTS in reasons(first_hour(explanations))


def test_second_shift_on_the_same_day_is_named() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100))
    roster = Solution((Assignment("e0", 0, "day", 4), Assignment("e1", 0, "night", 4)))

    explanations = explain_shortfall(instance_of(crew), roster)

    assert ViolationKind.MULTIPLE_SHIFTS_PER_DAY in reasons(first_hour(explanations))


def test_budget_is_named_when_one_more_shift_would_exceed_it() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100))
    roster = Solution((Assignment("e0", 0, "day", 4),))
    budget = 100 * 8 * 100

    explanations = explain_shortfall(instance_of(crew, budget=budget), roster)

    assert reasons(first_hour(explanations)) == {ViolationKind.OVER_BUDGET: 1}
    assert all(item.free_employees == () for item in explanations)


def test_a_proven_optimal_roster_leaves_nobody_free() -> None:
    instance = Instance(
        demand=(1,) * HOURS_PER_WEEK,
        employees=(Employee("e0", 100),),
        shift_types=(DAY,),
    )
    outcome = solve_roster(instance, PARAMS)

    explanations = explain_shortfall(instance, outcome.solution)

    assert outcome.phases[0].status is SolveStatus.OPTIMAL
    assert explanations
    assert all(item.free_employees == () for item in explanations)


def test_an_hour_no_shift_type_works_is_marked_uncoverable() -> None:
    instance = Instance(
        demand=(1,) * HOURS_PER_WEEK,
        employees=(Employee("e0", 100),),
        shift_types=(DAY,),
    )

    explanations = explain_shortfall(instance, Solution(()))
    night = next(item for item in explanations if item.hour == 3)
    morning = next(item for item in explanations if item.hour == 9)

    assert night.uncoverable
    assert night.blocked == ()
    assert not morning.uncoverable
    assert morning.free_employees == ("e0",)


def test_explanations_are_deterministic() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100, unavailable_days=frozenset({0})))
    roster = Solution((Assignment("e0", 0, "day", 4),))
    instance = instance_of(crew)

    assert explain_shortfall(instance, roster) == explain_shortfall(instance, roster)


def test_shortfall_does_not_depend_on_models_or_solvers() -> None:
    tree = ast.parse(Path(shortfall.__file__).read_text(encoding="utf-8"))
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    forbidden = ("shiftopt.models", "shiftopt.solvers")

    assert not any(name.startswith(forbidden) for name in modules if name)
