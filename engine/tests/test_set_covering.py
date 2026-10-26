from collections.abc import Callable

import pulp

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Instance, ShiftType
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.set_covering_pulp import solve_set_covering
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.solvers.pulp_backend import run_problem
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_WEEK, hour_of_week, shift_hours

PARAMS = SolveParams(num_workers=1, time_limit_seconds=30)


def coverage(counts: dict[tuple[int, str], float], instance: Instance) -> list[float]:
    covered = [0.0] * HOURS_PER_WEEK
    for (day, name), people in counts.items():
        shift = instance.shift_by_name(name)
        for hour in shift_hours(day, shift.start_hour, shift.length):
            covered[hour] += people
    return covered


def enumerated_break_optimum(instance: Instance, hourly_wage: int) -> float:
    """Oracle: enumerate every (day, shift, break position) column explicitly, the Dantzig form
    the implicit model is supposed to match. A column covers every hour of its shift except the
    break hour."""
    rules = instance.rules
    problem = pulp.LpProblem("enumerated", pulp.LpMinimize)
    columns: list[tuple[int, float, set[int]]] = []
    for day in range(DAYS_PER_WEEK):
        for shift in instance.shift_types:
            if shift.length > rules.max_daily_hours:
                continue
            hours = set(shift_hours(day, shift.start_hour, shift.length))
            cost = hourly_wage * shift.cost_per_wage_unit(rules)
            window = shift.break_window(rules)
            if not window:
                columns.append((len(columns), cost, hours))
            for offset in window:
                broken = hour_of_week(day, shift.start_hour + offset)
                columns.append((len(columns), cost, hours - {broken}))
    variables = [
        problem.add_variable(f"c_{index}", lowBound=0, cat=pulp.LpInteger)
        for index, _, _ in columns
    ]
    problem += pulp.lpSum(cost * variables[index] for index, cost, _ in columns)
    for hour in range(HOURS_PER_WEEK):
        problem += (
            pulp.lpSum(variables[index] for index, _, hours in columns if hour in hours)
            >= instance.demand[hour],
            f"cover_{hour}",
        )
    result = run_problem(problem, PARAMS, mip=True)
    assert result.objective is not None
    return result.objective


def test_three_shifts_cover_one_person_around_the_clock(
    build_instance: Callable[..., Instance],
) -> None:
    instance = build_instance(demand_per_hour=1)
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert outcome.result.status is SolveStatus.OPTIMAL
    assert sum(outcome.counts.values()) == 21
    assert outcome.result.objective == 7 * 100 * (2400 + 30 * 8)


def test_doubling_demand_doubles_head_count(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=2)
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert sum(outcome.counts.values()) == 42


def test_covering_meets_every_hour_demand(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=1)
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert all(value >= 1 for value in coverage(outcome.counts, instance))


def test_zero_demand_costs_nothing(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=0)
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert outcome.result.objective == 0
    assert all(value == 0 for value in outcome.counts.values())


def test_shift_longer_than_daily_limit_is_excluded() -> None:
    instance = Instance(
        demand=(1,) * HOURS_PER_WEEK,
        employees=(),
        shift_types=(ShiftType("long", 0, length=10),),
    )
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert outcome.result.status is SolveStatus.INFEASIBLE


def test_lp_relaxation_returns_nonnegative_duals(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=1)
    outcome = solve_set_covering(instance, hourly_wage=100, params=PARAMS, relax=True)
    assert outcome.duals is not None
    assert len(outcome.duals) == HOURS_PER_WEEK
    assert all(dual is not None and dual >= -1e-9 for dual in outcome.duals)
    assert sum(dual for dual in outcome.duals if dual is not None) > 0


def test_relaxation_is_a_lower_bound(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=1)
    relaxed = solve_set_covering(instance, hourly_wage=100, params=PARAMS, relax=True)
    integer = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    assert relaxed.result.objective is not None
    assert integer.result.objective is not None
    assert relaxed.result.objective <= integer.result.objective


def test_implicit_breaks_match_enumerated_columns(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=1)
    implicit = solve_with_implicit_breaks(instance, hourly_wage=100, params=PARAMS)
    assert implicit.result.objective == enumerated_break_optimum(instance, hourly_wage=100)


def test_implicit_breaks_match_enumerated_columns_on_peaked_demand() -> None:
    demand = tuple(2 if 8 <= hour % 24 < 16 else 1 for hour in range(HOURS_PER_WEEK))
    instance = Instance(
        demand=demand,
        employees=(),
        shift_types=(ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16)),
        rules=LaborRules(),
    )
    implicit = solve_with_implicit_breaks(instance, hourly_wage=100, params=PARAMS)
    assert implicit.result.objective == enumerated_break_optimum(instance, hourly_wage=100)


def test_breaks_never_make_the_head_count_cheaper(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=1)
    plain = solve_set_covering(instance, hourly_wage=100, params=PARAMS)
    implicit = solve_with_implicit_breaks(instance, hourly_wage=100, params=PARAMS)
    assert plain.result.objective is not None
    assert implicit.result.objective is not None
    assert implicit.result.objective >= plain.result.objective
