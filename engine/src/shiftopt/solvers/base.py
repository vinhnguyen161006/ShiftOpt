from dataclasses import dataclass
from enum import StrEnum


class SolveStatus(StrEnum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SolveParams:
    """Solver settings stored with every run. Identical instance, params and seed with
    num_workers = 1 must reproduce the same objective."""

    time_limit_seconds: float = 60.0
    relative_gap_limit: float = 0.01
    num_workers: int = 8
    random_seed: int = 0


@dataclass(frozen=True)
class SolveResult:
    """gap = |objective - bound| / max(1, |objective|); None when no solution was found."""

    status: SolveStatus
    objective: float | None
    bound: float | None
    gap: float | None
    wall_time_seconds: float
    solver: str
