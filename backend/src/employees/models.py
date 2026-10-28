from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class EmployeeRecord(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    hourly_wage: Mapped[int]
    unavailable_days: Mapped[list[int]] = mapped_column(JSON, default=list)
    preferred_days_off: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
