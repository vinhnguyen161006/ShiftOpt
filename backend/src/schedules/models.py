from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, enum_column


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SolveRun(Base):
    """One optimization run. instance_snapshot and params make it reproducible: the same
    snapshot, params and seed with one worker give the same objective."""

    __tablename__ = "solve_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    demand_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("demand_profiles.id", ondelete="SET NULL")
    )
    status: Mapped[RunStatus] = mapped_column(enum_column(RunStatus), default=RunStatus.QUEUED)
    solver: Mapped[str] = mapped_column(String(64), default="ortools-cp-sat")
    solve_status: Mapped[str | None] = mapped_column(String(32))
    params: Mapped[dict[str, float]] = mapped_column(JSON)
    instance_snapshot: Mapped[dict[str, object]] = mapped_column(JSON)
    assignments: Mapped[list[dict[str, object]] | None] = mapped_column(JSON)
    objective: Mapped[float | None]
    best_bound: Mapped[float | None]
    gap: Mapped[float | None]
    understaffed_hours: Mapped[int | None]
    wall_time_seconds: Mapped[float | None]
    solver_log: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
