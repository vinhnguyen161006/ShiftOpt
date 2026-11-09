from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class EmployeeRecord(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("owner_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(120))
    hourly_wage: Mapped[int]
    max_weekly_hours: Mapped[int | None]
    min_weekly_hours: Mapped[int | None]
    unavailable_days: Mapped[list[int]] = mapped_column(JSON, default=list)
    preferred_days_off: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
