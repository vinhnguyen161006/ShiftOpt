from datetime import datetime

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import ShiftType
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

    def _shift_type(self) -> ShiftType:
        return ShiftType(self.name, self.start_hour, self.length_hours)

    @property
    def night_hours(self) -> int:
        """Hours inside the default night window (Article 106), from the engine."""
        return self._shift_type().night_hours(LaborRules())

    @property
    def break_required(self) -> bool:
        """Whether the default rules require a rest break inside this shift (Article 109)."""
        return bool(self._shift_type().break_window(LaborRules()))
