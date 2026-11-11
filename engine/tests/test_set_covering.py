from collections.abc import Callable

from shiftopt.domain import Instance, ShiftType
from shiftopt.models.set_covering_pulp import solve_set_covering
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK, shift_hours

PARAMS = SolveParams(num_workers=1, time_limit_seconds=30)


def coverage(counts: dict[tuple[int, str], float], instance: Instance) -> list[float]:
    covered = [0.0] * HOURS_PER_WEEK
    for (day, name), people in counts.items():
        shift = instance.shift_by_name(name)
        for hour in shift_hours(day, shift.start_hour, shift.length):
            covered[hour] += people
    return covered


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
