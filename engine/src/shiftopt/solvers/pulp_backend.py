import math
from typing import Any

import highspy
import pulp

from shiftopt.solvers.base import (
    ModelInvalidError,
    SolveParams,
    SolveResult,
    SolveStatus,
    relative_gap,
)

SOLVER_NAME = "pulp-highs"

_HAS_SOLUTION = (
    highspy.HighsModelStatus.kOptimal,
    highspy.HighsModelStatus.kTimeLimit,
    highspy.HighsModelStatus.kIterationLimit,
    highspy.HighsModelStatus.kSolutionLimit,
    highspy.HighsModelStatus.kInterrupt,
    highspy.HighsModelStatus.kHighsInterrupt,
    highspy.HighsModelStatus.kObjectiveBound,
    highspy.HighsModelStatus.kObjectiveTarget,
)
_MODEL_ERRORS = (
    highspy.HighsModelStatus.kNotset,
    highspy.HighsModelStatus.kLoadError,
    highspy.HighsModelStatus.kModelError,
    highspy.HighsModelStatus.kPresolveError,
    highspy.HighsModelStatus.kSolveError,
    highspy.HighsModelStatus.kPostsolveError,
    highspy.HighsModelStatus.kUnbounded,
)


def run_problem(problem: pulp.LpProblem, params: SolveParams, *, mip: bool) -> SolveResult:
    """Solve a PuLP problem with HiGHS and map the status. Status comes from the HiGHS model
    status because PuLP status cannot tell a time-limited incumbent from a proven optimum."""
    solver = pulp.HiGHS(
        mip=mip,
        msg=params.log_search_progress,
        gapRel=params.relative_gap_limit,
        threads=params.num_workers,
        timeLimit=params.time_limit_seconds,
        random_seed=params.random_seed,
    )
    problem.solve(solver)
    highs = problem.solverModel
    model_status = highs.getModelStatus()
    if model_status in _MODEL_ERRORS:
        raise ModelInvalidError(highs.modelStatusToString(model_status))
    has_solution = model_status in _HAS_SOLUTION and highs.getSolution().value_valid
    status = _status_of(model_status, has_solution)
    objective = pulp.value(problem.objective) if has_solution else None
    bound = _bound_of(highs, mip, objective) if has_solution else None
    gap = relative_gap(objective, bound) if objective is not None and bound is not None else None
    return SolveResult(
        status=status,
        objective=objective,
        bound=bound,
        gap=gap,
        wall_time_seconds=highs.getRunTime(),
        solver=SOLVER_NAME,
        solver_version=pulp.__version__,
    )


def _status_of(model_status: Any, has_solution: bool) -> SolveStatus:
    if model_status == highspy.HighsModelStatus.kOptimal:
        return SolveStatus.OPTIMAL
    if model_status in (
        highspy.HighsModelStatus.kInfeasible,
        highspy.HighsModelStatus.kUnboundedOrInfeasible,
    ):
        return SolveStatus.INFEASIBLE
    return SolveStatus.FEASIBLE if has_solution else SolveStatus.UNKNOWN


def _bound_of(highs: highspy.Highs, mip: bool, objective: float | None) -> float | None:
    if not mip:
        return objective
    bound = highs.getInfo().mip_dual_bound
    return bound if math.isfinite(bound) else None
