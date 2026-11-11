from typing import Any

from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams

from src.schedules.snapshot import Snapshot, instance_from_snapshot, repair_from_snapshot


def to_solve_params(params: dict[str, float]) -> SolveParams:
    return SolveParams(
        time_limit_seconds=float(params["time_limit_seconds"]),
        relative_gap_limit=float(params["relative_gap_limit"]),
        num_workers=int(params["num_workers"]),
        random_seed=int(params["random_seed"]),
        cost_tolerance_percent=float(params.get("cost_tolerance_percent", 0.0)),
    )


def solve_snapshot(snapshot: Snapshot, params: dict[str, float]) -> dict[str, Any]:
    outcome = solve_roster(
        instance_from_snapshot(snapshot),
        to_solve_params(params),
        repair=repair_from_snapshot(snapshot),
    )
    result = outcome.result
    return {
        "solve_status": result.status.value,
        "objective": result.objective,
        "bound": result.bound,
        "gap": result.gap,
        "understaffed_hours": outcome.understaffed_hours,
        "wall_time_seconds": result.wall_time_seconds,
        "solver": result.solver,
        "solver_version": result.solver_version,
        "log": result.log,
        "assignments": [
            {
                "employee_code": assignment.employee_id,
                "day": assignment.day,
                "shift_name": assignment.shift_name,
            }
            for assignment in outcome.solution.assignments
        ],
    }
