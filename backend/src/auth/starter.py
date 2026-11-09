"""Starter data every new account receives, so a first visit can solve a schedule at once:
30 employees and three 8-hour shift templates. Demand still comes from the demand page."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.employees.models import EmployeeRecord
from src.shifts.models import ShiftTemplate

EMPLOYEE_COUNT = 30
HOURLY_WAGE = 100
PART_TIME_CODE = "E07"
PART_TIME_WEEKLY_HOURS = 24
SHIFT_TEMPLATES = (("\u0110\xeam", 0), ("Ng\xe0y", 8), ("T\u1ed1i", 16))
SHIFT_LENGTH_HOURS = 8


def starter_employees(owner_id: int) -> list[EmployeeRecord]:
    employees = []
    for index in range(1, EMPLOYEE_COUNT + 1):
        code = f"E{index:02d}"
        employees.append(
            EmployeeRecord(
                owner_id=owner_id,
                code=code,
                name=f"Employee {index}",
                hourly_wage=HOURLY_WAGE,
                max_weekly_hours=PART_TIME_WEEKLY_HOURS if code == PART_TIME_CODE else None,
                min_weekly_hours=None,
                unavailable_days=[],
                preferred_days_off=[],
            )
        )
    return employees


def starter_templates(owner_id: int) -> list[ShiftTemplate]:
    return [
        ShiftTemplate(
            owner_id=owner_id, name=name, start_hour=start, length_hours=SHIFT_LENGTH_HOURS
        )
        for name, start in SHIFT_TEMPLATES
    ]


def add_starter_data(session: AsyncSession, owner_id: int) -> None:
    """Adds the rows to the session without committing, so they land in the same transaction
    as the new account."""
    session.add_all([*starter_employees(owner_id), *starter_templates(owner_id)])
