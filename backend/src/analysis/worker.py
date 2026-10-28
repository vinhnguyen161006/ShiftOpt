from typing import Any

from shiftopt.domain import Instance
from shiftopt.sensitivity.lp_duals import compare_duals_with_marginal_cost, lp_relaxation_duals
from shiftopt.sensitivity.parametric import (
    aggregate_resolver,
    discrete_marginal_cost,
    roster_resolver,
    sweep_demand_multiplier,
)
from shiftopt.solvers.base import SolveParams

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
    raise ValueError(f"unknown analysis kind {kind}")


def _demand_sweep(
    instance: Instance, multipliers: list[float], params: SolveParams
) -> dict[str, Any]:
    points = sweep_demand_multiplier(instance, multipliers, roster_resolver(params))
    return {
        "points": [
            {
                "multiplier": point.multiplier,
                "solve_status": point.evaluation.result.status.value,
                "proven": point.proven,
                "labor_cost": point.evaluation.labor_cost,
                "understaffed_hours": point.evaluation.understaffed_hours,
                "staffed_hours": point.evaluation.staffed_hours,
            }
            for point in points
        ]
    }


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
