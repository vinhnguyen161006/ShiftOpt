from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.analysis.models import AnalysisKind
from src.schedules.models import RunStatus
from src.schedules.schemas import SolveRequest

DEFAULT_MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]


class DemandSweepRequest(BaseModel):
    solve: SolveRequest
    multipliers: list[float] = Field(
        default_factory=lambda: list(DEFAULT_MULTIPLIERS), min_length=1
    )


class MarginalCostRequest(BaseModel):
    solve: SolveRequest


class LpDualsRequest(BaseModel):
    solve: SolveRequest
    hourly_wage: int = Field(gt=0)


class SweepPoint(BaseModel):
    multiplier: float
    solve_status: str
    objective: float | None
    understaffed_hours: int | None
    total_staff_hours: int | None


class DemandSweepResult(BaseModel):
    points: list[SweepPoint]


class MarginalCostResult(BaseModel):
    marginal_cost_by_hour: list[float | None] = Field(min_length=168, max_length=168)


class LpDualsResult(BaseModel):
    approximate: bool = True
    duals_by_hour: list[float] = Field(min_length=168, max_length=168)


class AnalysisAccepted(BaseModel):
    job_id: int
    status: RunStatus


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: AnalysisKind
    status: RunStatus
    result: dict[str, object] | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None
