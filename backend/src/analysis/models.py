from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, enum_column
from src.schedules.models import RunStatus


class AnalysisKind(StrEnum):
    DEMAND_SWEEP = "demand_sweep"
    MARGINAL_COST = "marginal_cost"
    LP_DUALS = "lp_duals"


class AnalysisRun(Base):
    """Sensitivity analyses re-solve the model many times, so they are jobs like solve runs."""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[AnalysisKind] = mapped_column(enum_column(AnalysisKind))
    base_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("solve_runs.id", ondelete="SET NULL")
    )
    status: Mapped[RunStatus] = mapped_column(enum_column(RunStatus), default=RunStatus.QUEUED)
    request: Mapped[dict[str, object]] = mapped_column(JSON)
    result: Mapped[dict[str, object] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
