import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from itertools import repeat
from typing import Any

from shiftopt.baseline import greedy_resolver
from shiftopt.domain import Instance
from shiftopt.kpi import labor_cost
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.sensitivity.lp_duals import compare_duals_with_marginal_cost, lp_relaxation_duals
from shiftopt.sensitivity.parametric import (
    Evaluation,
    aggregate_resolver,
    discrete_marginal_cost,
    roster_resolver,
    scale_demand,
)
from shiftopt.sensitivity.scenarios import StaffingAssumption, sweep_staffing_assumption
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.staffing.latent_demand import zero_night_load

from src.analysis.models import AnalysisKind
from src.schedules.snapshot import instance_from_snapshot
from src.schedules.worker import to_solve_params


def run_analysis(kind: str, request: dict[str, Any]) -> dict[str, Any]:
    instance = instance_from_snapshot(request["snapshot"])
    params = to_solve_params(request["params"])
    if kind == AnalysisKind.DEMAND_SWEEP:
        return _demand_sweep(instance, request["multipliers"], params)
    if kind == AnalysisKind.MARGINAL_COST:
        return _marginal_cost(instance, int(request["hourly_wage"]), params)
    if kind == AnalysisKind.LP_DUALS:
        return _lp_duals(instance, int(request["hourly_wage"]), params)
    if kind == AnalysisKind.STAFFING_SWEEP:
        return _staffing_sweep(instance, request, params)
    if kind == AnalysisKind.BASELINE_COMPARE:
        return _baseline_compare(instance, params)
    if kind == AnalysisKind.FAIRNESS_SWEEP:
        return _fairness_sweep(instance, request["tolerances"], params)
    raise ValueError(f"unknown analysis kind {kind}")


def _staffing_sweep(
    instance: Instance, request: dict[str, Any], params: SolveParams
) -> dict[str, Any]:
    load = tuple(request["load"])
    if not request["night_from_sales"]:
        load, _ = zero_night_load(load, instance.rules)
    base = StaffingAssumption(**request["base"])
    points = sweep_staffing_assumption(
        instance,
        load,
        base,
        request["assumption"],
        request["values"],
        roster_resolver(params),
    )
    return {
        "assumption": request["assumption"],
        "points": [_staffing_row(value, evaluation) for value, evaluation in points],
    }


def _staffing_row(value: float, evaluation: Evaluation) -> dict[str, Any]:
    return {
        "value": value,
        "solve_status": evaluation.result.status.value,
        "proven": evaluation.proven,
        "labor_cost": evaluation.labor_cost,
        "understaffed_hours": evaluation.understaffed_hours,
        "staffed_hours": evaluation.staffed_hours,
    }


def parallel_points(point_count: int, workers_per_point: int) -> int:
    """How many sweep points to solve at once: as many as the CPUs hold when each point uses
    workers_per_point threads, never more than the number of points."""
    capacity = (os.cpu_count() or 1) // max(1, workers_per_point)
    return max(1, min(point_count, capacity))


def solve_sweep_point(instance: Instance, multiplier: float, params: SolveParams) -> dict[str, Any]:
    scaled = scale_demand(instance, multiplier)
    evaluation = roster_resolver(params)(scaled)
    return _sweep_row(multiplier, evaluation, scaled)


def _sweep_row(multiplier: float, evaluation: Evaluation, scaled: Instance) -> dict[str, Any]:
    return {
        "multiplier": multiplier,
        "solve_status": evaluation.result.status.value,
        "proven": evaluation.proven,
        "labor_cost": evaluation.labor_cost,
        "understaffed_hours": evaluation.understaffed_hours,
        "staffed_hours": evaluation.staffed_hours,
        "staff_by_hour": _optional_list(evaluation.staff_by_hour),
        "required_by_hour": list(scaled.demand),
    }


def _demand_sweep(
    instance: Instance, multipliers: list[float], params: SolveParams
) -> dict[str, Any]:
    parallel = parallel_points(len(multipliers), params.num_workers)
    if parallel == 1:
        rows = [solve_sweep_point(instance, multiplier, params) for multiplier in multipliers]
        return {"points": rows}
    with ProcessPoolExecutor(max_workers=parallel) as pool:
        rows = list(pool.map(solve_sweep_point, repeat(instance), multipliers, repeat(params)))
    return {"points": rows}


def _optional_list(values: tuple[int, ...] | None) -> list[int] | None:
    return None if values is None else list(values)


def _marginal_cost(instance: Instance, hourly_wage: int, params: SolveParams) -> dict[str, Any]:
    table = discrete_marginal_cost(instance, aggregate_resolver(hourly_wage, params))
    lp = lp_relaxation_duals(instance, hourly_wage, params)
    comparison = compare_duals_with_marginal_cost(lp, table)
    return {
        "base_cost": table.base.labor_cost,
        "base_status": table.base.result.status.value,
        "marginal_cost_by_hour": [entry.marginal_cost for entry in comparison],
        "proven_by_hour": [entry.proven for entry in comparison],
        "lp_dual_by_hour": [entry.lp_dual for entry in comparison],
        "approximate": True,
        "label": lp.label,
    }


def _lp_duals(instance: Instance, hourly_wage: int, params: SolveParams) -> dict[str, Any]:
    lp = lp_relaxation_duals(instance, hourly_wage, params)
    return {
        "approximate": True,
        "label": lp.label,
        "duals_by_hour": list(lp.duals),
        "missing_hours": list(lp.missing_hours),
        "lp_objective": lp.lp_objective,
    }


def _baseline_compare(instance: Instance, params: SolveParams) -> dict[str, Any]:
    return {
        "points": [
            _baseline_row("cpsat", roster_resolver(params)(instance)),
            _baseline_row("greedy", greedy_resolver()(instance)),
        ]
    }


def solve_fairness_point(
    instance: Instance, tolerance: float, params: SolveParams
) -> dict[str, Any]:
    outcome = solve_roster(instance, replace(params, cost_tolerance_percent=tolerance))
    solved = outcome.understaffed_hours is not None
    return {
        "tolerance_percent": tolerance,
        "solve_status": outcome.result.status.value,
        "proven": outcome.result.status is SolveStatus.OPTIMAL,
        "labor_cost": float(labor_cost(instance, outcome.solution)) if solved else None,
        "night_spread": outcome.night_spread,
        "hours_spread": outcome.hours_spread,
        "understaffed_hours": outcome.understaffed_hours,
    }


def _fairness_sweep(
    instance: Instance, tolerances: list[float], params: SolveParams
) -> dict[str, Any]:
    parallel = parallel_points(len(tolerances), params.num_workers)
    if parallel == 1:
        rows = [solve_fairness_point(instance, tolerance, params) for tolerance in tolerances]
    else:
        with ProcessPoolExecutor(max_workers=parallel) as pool:
            rows = list(
                pool.map(solve_fairness_point, repeat(instance), tolerances, repeat(params))
            )
    base = next(
        (
            row["labor_cost"]
            for row in rows
            if row["tolerance_percent"] == 0 and row["labor_cost"] is not None
        ),
        None,
    )
    for row in rows:
        row["cost_increase_percent"] = (
            None
            if base is None or row["labor_cost"] is None
            else 100 * (row["labor_cost"] - base) / base
        )
    return {"points": rows}


def _baseline_row(method: str, evaluation: Evaluation) -> dict[str, Any]:
    return {
        "method": method,
        "solve_status": evaluation.result.status.value,
        "proven": evaluation.proven,
        "labor_cost": evaluation.labor_cost,
        "understaffed_hours": evaluation.understaffed_hours,
        "staffed_hours": evaluation.staffed_hours,
    }
