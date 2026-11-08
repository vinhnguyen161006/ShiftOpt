from dataclasses import dataclass, replace
from enum import StrEnum


class SolveStatus(StrEnum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


class ModelInvalidError(RuntimeError):
    """The solver rejected the model. This is a programming error, never a user input error."""


MAX_COST_TOLERANCE_PERCENT = 10.0


@dataclass(frozen=True)
class SolveParams:
    """Solver settings stored with every run. Identical instance, params and seed with
    num_workers = 1 must reproduce the same objective. cost_tolerance_percent lets the labour cost
    tier rise by that percentage above its optimum so that the later fairness tiers can improve;
    0 keeps the strict lexicographic order."""

    time_limit_seconds: float = 60.0
    relative_gap_limit: float = 0.01
    num_workers: int = 8
    random_seed: int = 0
    log_search_progress: bool = False
    cost_tolerance_percent: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.cost_tolerance_percent <= MAX_COST_TOLERANCE_PERCENT:
            raise ValueError(
                f"cost_tolerance_percent must be between 0 and {MAX_COST_TOLERANCE_PERCENT}"
            )


@dataclass(frozen=True)
class SolveResult:
    """gap = |objective - bound| / max(1, |objective|); None when no solution was found."""

    status: SolveStatus
    objective: float | None
    bound: float | None
    gap: float | None
    wall_time_seconds: float
    solver: str
    solver_version: str
    log: str = ""


def relative_gap(objective: float, bound: float) -> float:
    return abs(objective - bound) / max(1.0, abs(objective))


def with_time_share(params: SolveParams, share: int) -> SolveParams:
    return replace(params, time_limit_seconds=params.time_limit_seconds / share)


def combine_tiers(results: tuple[SolveResult, ...], stage_count: int) -> SolveResult:
    """Combine the per-tier results of a lexicographic solve. OPTIMAL only when every tier proves
    optimality; otherwise FEASIBLE with the objective, bound and gap of the last tier that returned
    a solution. Wall time is the sum over tiers."""
    last = next((result for result in reversed(results) if result.objective is not None), None)
    if last is None:
        status = SolveStatus.UNKNOWN
    elif len(results) == stage_count and all(
        result.status is SolveStatus.OPTIMAL for result in results
    ):
        status = SolveStatus.OPTIMAL
    else:
        status = SolveStatus.FEASIBLE
    return SolveResult(
        status=status,
        objective=last.objective if last else None,
        bound=last.bound if last else None,
        gap=last.gap if last else None,
        wall_time_seconds=sum(result.wall_time_seconds for result in results),
        solver=results[0].solver,
        solver_version=results[0].solver_version,
        log="\n".join(result.log for result in results),
    )


DEFAULT_PARAMS = SolveParams()
