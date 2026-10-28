from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.analysis.models import AnalysisKind
from src.schedules.models import RunStatus
from src.schedules.schemas import SolveRequest

DEFAULT_MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
MAX_SWEEP_POINTS = 20
HOURS_OF_WEEK = 168
APPROXIMATE_LABEL = "LP relaxation dual: an approximation, the integrality gap can be large"

Multiplier = Annotated[float, Field(gt=0, le=3)]


class DemandSweepRequest(BaseModel):
    solve: SolveRequest
    multipliers: list[Multiplier] = Field(
        default_factory=lambda: list(DEFAULT_MULTIPLIERS),
        min_length=1,
        max_length=MAX_SWEEP_POINTS,
    )


class MarginalCostRequest(BaseModel):
    solve: SolveRequest
    hourly_wage: int = Field(gt=0)


class LpDualsRequest(BaseModel):
    solve: SolveRequest
    hourly_wage: int = Field(gt=0)


class SweepPoint(BaseModel):
    multiplier: float
    solve_status: str
    proven: bool
    labor_cost: float | None
    understaffed_hours: int | None
    staffed_hours: int | None


class DemandSweepResult(BaseModel):
    points: list[SweepPoint]


class MarginalCostResult(BaseModel):
    base_cost: float | None
    base_status: str
    marginal_cost_by_hour: list[float | None] = Field(
        min_length=HOURS_OF_WEEK, max_length=HOURS_OF_WEEK
    )
    proven_by_hour: list[bool] = Field(min_length=HOURS_OF_WEEK, max_length=HOURS_OF_WEEK)
    lp_dual_by_hour: list[float] = Field(min_length=HOURS_OF_WEEK, max_length=HOURS_OF_WEEK)
    approximate: bool = True
    label: str = APPROXIMATE_LABEL


class LpDualsResult(BaseModel):
    approximate: bool = True
    label: str = APPROXIMATE_LABEL
    duals_by_hour: list[float] = Field(min_length=HOURS_OF_WEEK, max_length=HOURS_OF_WEEK)
    missing_hours: list[int]
    lp_objective: float


class AnalysisAccepted(BaseModel):
    job_id: int
    status: RunStatus


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: AnalysisKind
    status: RunStatus
    result: DemandSweepResult | MarginalCostResult | LpDualsResult | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None
