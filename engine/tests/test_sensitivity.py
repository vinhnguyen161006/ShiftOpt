from collections.abc import Callable

import pytest

from shiftopt import kpi
from shiftopt.domain import Instance
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.sensitivity.lp_duals import (
    APPROXIMATE_LABEL,
    compare_duals_with_marginal_cost,
    lp_relaxation_duals,
    normalize_duals,
)
from shiftopt.sensitivity.parametric import (
    DEFAULT_MULTIPLIERS,
    Evaluation,
    Resolver,
    aggregate_resolver,
    discrete_marginal_cost,
    roster_resolver,
    scale_demand,
    sweep_demand_multiplier,
)
from shiftopt.sensitivity.scenarios import (
    DemandScenario,
    StaffingAssumption,
    apply_demand_scenario,
    compare_scenarios,
    promotion_scenario,
    sweep_staffing_assumption,
)
from shiftopt.solvers.base import SolveParams, SolveResult, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK

InstanceFactory = Callable[..., Instance]

PARAMS = SolveParams(time_limit_seconds=20.0, num_workers=1, random_seed=0)
WAGE = 100


def _result(status: SolveStatus, objective: float | None = None) -> SolveResult:
    return SolveResult(
        status=status,
        objective=objective,
        bound=objective,
        gap=None if objective is None else 0.0,
        wall_time_seconds=0.0,
        solver="fake",
        solver_version="0",
    )


def _feasible_resolver(instance: Instance) -> Evaluation:
    return Evaluation(_result(SolveStatus.FEASIBLE, 5.0), 5.0, 0, 8)


def _cost(evaluation: Evaluation) -> float:
    assert evaluation.labor_cost is not None
    return evaluation.labor_cost


def test_scale_demand_rounds_up_with_tolerance(build_instance: InstanceFactory) -> None:
    scaled = scale_demand(build_instance(demand_per_hour=10), 1.1)
    assert scaled.demand[0] == 11


def test_scale_demand_rejects_non_positive_multiplier(build_instance: InstanceFactory) -> None:
    with pytest.raises(ValueError, match="positive"):
        scale_demand(build_instance(), 0.0)


def test_cost_curve_is_monotone_in_demand_multiplier(build_instance: InstanceFactory) -> None:
    points = sweep_demand_multiplier(
        build_instance(demand_per_hour=2),
        (0.8, 1.0, 1.3),
        aggregate_resolver(WAGE, PARAMS),
    )
    assert all(point.proven for point in points)
    costs = [_cost(point.evaluation) for point in points]
    assert costs == sorted(costs)
    assert costs[-1] > costs[0]


def test_default_multipliers_cover_the_range() -> None:
    assert DEFAULT_MULTIPLIERS[0] == 0.8
    assert DEFAULT_MULTIPLIERS[-1] == 1.3


def test_sweep_flags_feasible_points_as_not_proven(build_instance: InstanceFactory) -> None:
    points = sweep_demand_multiplier(build_instance(), (1.0, 1.1), _feasible_resolver)
    assert not any(point.proven for point in points)


def test_marginal_cost_matches_hand_example(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, wage=WAGE)
    table = discrete_marginal_cost(instance, aggregate_resolver(WAGE, PARAMS, with_breaks=False))
    night_shift_cost_per_wage_unit = 100 * 8 + 30 * 6
    assert table.hours[3].delta == WAGE * night_shift_cost_per_wage_unit
    assert table.hours[3].proven


def test_discrete_marginal_cost_is_never_negative(build_instance: InstanceFactory) -> None:
    table = discrete_marginal_cost(
        build_instance(demand_per_hour=1), aggregate_resolver(WAGE, PARAMS)
    )
    assert len(table.hours) == HOURS_PER_WEEK
    assert all(entry.proven for entry in table.hours)
    assert all(entry.delta is not None and entry.delta >= 0 for entry in table.hours)


def test_marginal_cost_flags_feasible_solves_as_not_proven(
    build_instance: InstanceFactory,
) -> None:
    table = discrete_marginal_cost(build_instance(), _feasible_resolver)
    assert not any(entry.proven for entry in table.hours)


def test_lp_duals_satisfy_strong_duality(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1)
    lp = lp_relaxation_duals(instance, WAGE, PARAMS)
    assert len(lp.duals) == HOURS_PER_WEEK
    assert lp.missing_hours == ()
    assert lp.approximate is True
    assert lp.label == APPROXIMATE_LABEL
    assert all(dual >= -1e-9 for dual in lp.duals)
    weighted = sum(dual * demand for dual, demand in zip(lp.duals, instance.demand, strict=True))
    assert weighted == pytest.approx(lp.lp_objective, abs=1e-6)


def test_lp_dual_comparison_has_one_row_per_hour(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1)
    lp = lp_relaxation_duals(instance, WAGE, PARAMS)
    table = discrete_marginal_cost(instance, aggregate_resolver(WAGE, PARAMS))
    rows = compare_duals_with_marginal_cost(lp, table)
    assert len(rows) == HOURS_PER_WEEK
    assert rows[0].lp_dual == lp.duals[0]
    assert rows[0].marginal_cost == table.hours[0].delta


def test_normalize_duals_replaces_none_and_lists_hours() -> None:
    duals, missing = normalize_duals([1.0, None, 2.0])
    assert duals == (1.0, 0.0, 2.0)
    assert missing == (1,)


def test_demand_scenario_scales_only_the_chosen_day(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1)
    scenario = DemandScenario("double_tuesday", {1: 2.0}, source="test")
    scenario_instance = apply_demand_scenario(instance, scenario)
    assert scenario_instance.demand[0] == 1
    assert scenario_instance.demand[24] == 2
    assert scenario_instance.demand[47] == 2
    assert scenario_instance.demand[48] == 1
    assert instance.demand[24] == 1


@pytest.mark.parametrize(
    "scenario",
    [
        DemandScenario("bad_day", {7: 1.5}, source="test"),
        DemandScenario("bad_factor", {0: 0.0}, source="test"),
    ],
)
def test_demand_scenario_rejects_invalid_input(
    build_instance: InstanceFactory, scenario: DemandScenario
) -> None:
    with pytest.raises(ValueError, match="scenario"):
        apply_demand_scenario(build_instance(), scenario)


def test_promotion_scenario_carries_a_source() -> None:
    scenario = promotion_scenario((5, 6))
    assert scenario.day_multipliers == {5: 1.43, 6: 1.43}
    assert scenario.source


def test_compare_scenarios_puts_baseline_first_and_promotion_costs_more(
    build_instance: InstanceFactory,
) -> None:
    rows = compare_scenarios(
        build_instance(demand_per_hour=2),
        [promotion_scenario((0,))],
        aggregate_resolver(WAGE, PARAMS),
    )
    assert [name for name, _ in rows] == ["baseline", "promotion"]
    assert _cost(rows[1][1]) > _cost(rows[0][1])


def test_staffing_assumption_sweep_raises_cost_with_alpha(
    build_instance: InstanceFactory,
) -> None:
    points = sweep_staffing_assumption(
        build_instance(demand_per_hour=0),
        load=(1.0,) * HOURS_PER_WEEK,
        base=StaffingAssumption(),
        field="alpha",
        values=(1.0, 2.0),
        resolver=aggregate_resolver(WAGE, PARAMS, with_breaks=False),
    )
    assert _cost(points[1][1]) > _cost(points[0][1])


def test_staffing_sweep_rejects_unknown_field_and_fractional_floor(
    build_instance: InstanceFactory,
) -> None:
    template = build_instance(demand_per_hour=0)
    load = (1.0,) * HOURS_PER_WEEK
    resolver: Resolver = _feasible_resolver
    with pytest.raises(ValueError, match="field"):
        sweep_staffing_assumption(template, load, StaffingAssumption(), "rate", (1.0,), resolver)
    with pytest.raises(ValueError, match="whole"):
        sweep_staffing_assumption(
            template, load, StaffingAssumption(), "min_staff", (0.5,), resolver
        )


def test_roster_resolver_reports_cost_from_kpi(build_instance: InstanceFactory) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=6)
    outcome = solve_roster(instance, PARAMS)
    evaluation = roster_resolver(PARAMS)(instance)
    assert evaluation.labor_cost == kpi.labor_cost(instance, outcome.solution)
    assert evaluation.understaffed_hours == outcome.understaffed_hours
    assert evaluation.staffed_hours == sum(
        instance.shift_by_name(assignment.shift_name).length
        for assignment in outcome.solution.assignments
    )
