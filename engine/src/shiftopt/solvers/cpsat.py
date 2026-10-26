from dataclasses import replace
from importlib.metadata import version

from ortools.sat.python import cp_model

from shiftopt.solvers.base import (
    ModelInvalidError,
    SolveParams,
    SolveResult,
    SolveStatus,
    relative_gap,
)

SOLVER_NAME = "ortools-cp-sat"

_STATUS_MAP = {
    cp_model.OPTIMAL: SolveStatus.OPTIMAL,
    cp_model.FEASIBLE: SolveStatus.FEASIBLE,
    cp_model.INFEASIBLE: SolveStatus.INFEASIBLE,
    cp_model.UNKNOWN: SolveStatus.UNKNOWN,
}


def with_time_share(params: SolveParams, share: int) -> SolveParams:
    return replace(params, time_limit_seconds=params.time_limit_seconds / share)


def run_cp_model(
    model: cp_model.CpModel, params: SolveParams
) -> tuple[cp_model.CpSolver, SolveResult]:
    """Solve a CP-SAT model with the shared settings. Returns the solver so the caller can read
    variable values. MODEL_INVALID raises ModelInvalidError because it is a programming error."""
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = params.time_limit_seconds
    solver.parameters.relative_gap_limit = params.relative_gap_limit
    solver.parameters.num_workers = params.num_workers
    solver.parameters.random_seed = params.random_seed
    solver.parameters.log_search_progress = params.log_search_progress
    log_lines: list[str] = []
    solver.log_callback = log_lines.append
    status = solver.solve(model)
    if status == cp_model.MODEL_INVALID:
        raise ModelInvalidError(model.validate())
    mapped = _STATUS_MAP[status]
    has_solution = mapped in (SolveStatus.OPTIMAL, SolveStatus.FEASIBLE)
    objective = solver.objective_value if has_solution else None
    bound = solver.best_objective_bound if has_solution else None
    gap = relative_gap(objective, bound) if objective is not None and bound is not None else None
    return solver, SolveResult(
        status=mapped,
        objective=objective,
        bound=bound,
        gap=gap,
        wall_time_seconds=solver.wall_time,
        solver=SOLVER_NAME,
        solver_version=version("ortools"),
        log="\n".join(log_lines),
    )
