from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ShiftTemplate(Base):
    __tablename__ = "shift_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    start_hour: Mapped[int]
    length_hours: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
