from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schedules.models import RunStatus


class SolveRequest(BaseModel):
    demand_profile_id: int
    shift_template_ids: list[int] = Field(min_length=1)
    employee_ids: list[int] | None = None
    time_limit_seconds: float = Field(60.0, gt=0)
    relative_gap_limit: float = Field(0.01, ge=0, le=1)
    num_workers: int = Field(8, ge=1)
    random_seed: int = 0


class JobAccepted(BaseModel):
    job_id: int
    status: RunStatus


class AssignmentRead(BaseModel):
    employee_code: str
    day: int = Field(ge=0, le=6)
    shift_name: str


class SolveRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    demand_profile_id: int | None
    status: RunStatus
    solver: str
    solve_status: str | None
    params: dict[str, float]
    assignments: list[AssignmentRead] | None
    objective: float | None
    best_bound: float | None
    gap: float | None
    understaffed_hours: int | None
    wall_time_seconds: float | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class ViolationRead(BaseModel):
    kind: str
    employee_code: str
    detail: str


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
    staff_by_hour: list[int] = Field(min_length=168, max_length=168)
    required_by_hour: list[int] = Field(min_length=168, max_length=168)
