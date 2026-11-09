from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator
from shiftopt.diagnostics import WarningKind

from src.schedules.models import RunStatus

WeekDay = Annotated[int, Field(ge=0, le=6)]


class SolveSettings(BaseModel):
    time_limit_seconds: float = Field(60.0, gt=0)
    relative_gap_limit: float = Field(0.01, ge=0, le=1)
    num_workers: int = Field(8, ge=1)
    random_seed: int = 0
    cost_tolerance_percent: float = Field(0.0, ge=0, le=10)


class SolveRequest(SolveSettings):
    demand_profile_id: int
    shift_template_ids: list[int] = Field(min_length=1, max_length=50)
    employee_ids: list[int] | None = Field(default=None, max_length=500)
    max_weekly_hours: int = Field(48, ge=1, le=168)
    max_consecutive_days: int = Field(6, ge=1, le=6)


class JobAccepted(BaseModel):
    job_id: int
    status: RunStatus


class PreSolveWarningRead(BaseModel):
    kind: WarningKind
    detail: str
    employee_id: str | None


class PreviewWarningsRead(BaseModel):
    warnings: list[PreSolveWarningRead]


class AssignmentRead(BaseModel):
    employee_code: str
    day: int = Field(ge=0, le=6)
    shift_name: str
    break_offset: int | None = None


class AssignmentWrite(BaseModel):
    employee_code: str = Field(min_length=1, max_length=32)
    day: int = Field(ge=0, le=6)
    shift_name: str = Field(min_length=1, max_length=64)
    break_offset: int | None = Field(default=None, ge=0, le=23)


class ManualEditRequest(BaseModel):
    assignments: list[AssignmentWrite] = Field(max_length=2000)


class AbsenceWrite(BaseModel):
    employee_code: str = Field(min_length=1, max_length=32)
    days: list[WeekDay] = Field(min_length=1, max_length=7)


class RerosterRequest(BaseModel):
    employee_code: str = Field(min_length=1, max_length=32)
    absent_days: list[WeekDay] = Field(min_length=1, max_length=7)
    from_day: WeekDay | None = None

    @field_validator("absent_days")
    @classmethod
    def _distinct_days(cls, days: list[int]) -> list[int]:
        if len(set(days)) != len(days):
            raise ValueError("absent_days must not repeat a day")
        return sorted(days)


class ScheduleChangesRead(BaseModel):
    kept: list[AssignmentRead]
    added: list[AssignmentRead]
    removed: list[AssignmentRead]


class RepairRequest(SolveSettings):
    from_day: WeekDay
    absences: list[AbsenceWrite] = Field(default_factory=list, max_length=500)
    pinned: list[AssignmentWrite] = Field(default_factory=list, max_length=2000)
    demand_profile_id: int | None = None


class ReplacementRead(BaseModel):
    employee_code: str
    shift_name: str
    break_offset: int | None
    extra_cost: int
    weekly_hours: int
    prefers_off: bool


class ShiftTypeRead(BaseModel):
    name: str
    start_hour: int
    length: int


class SolveRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_codes: list[str]
    shift_types: list[ShiftTypeRead]
    demand_profile_id: int | None
    parent_run_id: int | None
    status: RunStatus
    solver: str
    solver_version: str | None
    solve_status: str | None
    params: dict[str, float]
    assignments: list[AssignmentRead] | None
    repair_from_day: int | None
    baseline_assignments: list[AssignmentRead] | None
    changes: int | None
    objective: float | None
    best_bound: float | None
    gap: float | None
    understaffed_hours: int | None
    hard_violations: int | None
    wall_time_seconds: float | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class ViolationRead(BaseModel):
    kind: str
    employee_code: str
    detail: str
    day: int | None
    legal_basis: str


class ComplianceRead(BaseModel):
    run_id: int
    violations: list[ViolationRead]


class KpiRead(BaseModel):
    run_id: int
    coverage_ratio: float
    understaffed_hours: int
    overstaffed_hours: int
    schedule_efficiency: float
    labor_cost: int
    night_premium_cost: int
    night_shift_stddev: float
    weekend_shift_stddev: float
    hours_spread: int
    hard_violations: int
    staff_by_hour: list[int] = Field(min_length=168, max_length=168)
    required_by_hour: list[int] = Field(min_length=168, max_length=168)
