from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.analysis.models import AnalysisKind
from src.schedules.models import RunStatus
from src.schedules.schemas import SolveRequest

DEFAULT_MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
MAX_SWEEP_POINTS = 20
HOURS_OF_WEEK = 168
APPROXIMATE_LABEL = "LP relaxation dual: an approximation, the integrality gap can be large"
STAFFING_LABEL = "Team conversion assumption, not staffing data from the source"
STAFFING_FLOORS = ("min_staff", "night_min_staff")
BASELINE_LABEL = "Greedy is a heuristic for comparison, not proven optimal"

Multiplier = Annotated[float, Field(gt=0, le=3)]
StaffingField = Literal["alpha", "productivity", "min_staff", "night_min_staff"]
StaffingValue = Annotated[float, Field(gt=0, le=1000)]


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


class StaffingSweepRequest(BaseModel):
    solve: SolveRequest
    assumption: StaffingField
    values: list[StaffingValue] = Field(min_length=1, max_length=MAX_SWEEP_POINTS)

    @model_validator(mode="after")
    def check_floors_are_whole(self) -> "StaffingSweepRequest":
        if self.assumption in STAFFING_FLOORS and any(
            not value.is_integer() for value in self.values
        ):
            raise ValueError(f"{self.assumption} values must be whole numbers")
        return self


class BaselineCompareRequest(BaseModel):
    solve: SolveRequest


class BaselineRow(BaseModel):
    method: Literal["cpsat", "greedy"]
    solve_status: str
    proven: bool
    labor_cost: float | None
    understaffed_hours: int | None
    staffed_hours: int | None


class BaselineCompareResult(BaseModel):
    label: str = BASELINE_LABEL
    points: list[BaselineRow]


class SweepPoint(BaseModel):
    multiplier: float
    solve_status: str
    proven: bool
    labor_cost: float | None
    understaffed_hours: int | None
    staffed_hours: int | None
    staff_by_hour: list[int] | None = None
    required_by_hour: list[int] | None = None


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


class StaffingSweepPoint(BaseModel):
    value: float
    solve_status: str
    proven: bool
    labor_cost: float | None
    understaffed_hours: int | None
    staffed_hours: int | None


class StaffingSweepResult(BaseModel):
    assumption: StaffingField
    label: str = STAFFING_LABEL
    points: list[StaffingSweepPoint]


class AnalysisAccepted(BaseModel):
    job_id: int
    status: RunStatus


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: AnalysisKind
    status: RunStatus
    result: (
        DemandSweepResult
        | MarginalCostResult
        | LpDualsResult
        | StaffingSweepResult
        | BaselineCompareResult
        | None
    )
    error: str | None
    created_at: datetime
    finished_at: datetime | None
