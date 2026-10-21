from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, enum_column


class DemandSource(StrEnum):
    MANUAL = "manual"
    CSV = "csv"
    FRESHRETAILNET = "freshretailnet"
    CALL_CENTER = "call_center"


class StaffingMode(StrEnum):
    LINEAR = "linear"
    ERLANG = "erlang"


class DemandProfile(Base):
    __tablename__ = "demand_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source: Mapped[DemandSource] = mapped_column(enum_column(DemandSource))
    mode: Mapped[StaffingMode] = mapped_column(enum_column(StaffingMode))
    required_staff: Mapped[list[int]] = mapped_column(JSON)
    conversion_params: Mapped[dict[str, float]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
