from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import commit_unique
from src.employees.models import EmployeeRecord
from src.employees.schemas import EmployeeCreate, EmployeeUpdate
from src.exceptions import InstanceTooLargeError, NotFoundError

DUPLICATE_CODE = "employee code already exists"


async def list_employees(session: AsyncSession) -> list[EmployeeRecord]:
    result = await session.scalars(select(EmployeeRecord).order_by(EmployeeRecord.code))
    return list(result)


async def get_employee(session: AsyncSession, employee_id: int) -> EmployeeRecord:
    employee = await session.get(EmployeeRecord, employee_id)
    if employee is None:
        raise NotFoundError(f"employee {employee_id} not found")
    return employee


async def create_employee(session: AsyncSession, payload: EmployeeCreate) -> EmployeeRecord:
    count = await session.scalar(select(func.count(EmployeeRecord.id)))
    if (count or 0) >= get_settings().max_employees:
        raise InstanceTooLargeError(f"at most {get_settings().max_employees} employees are allowed")
    employee = EmployeeRecord(**payload.model_dump())
    session.add(employee)
    await commit_unique(session, DUPLICATE_CODE)
    await session.refresh(employee)
    return employee


async def update_employee(
    session: AsyncSession, employee_id: int, payload: EmployeeUpdate
) -> EmployeeRecord:
    employee = await get_employee(session, employee_id)
    for field, value in payload.model_dump().items():
        setattr(employee, field, value)
    await commit_unique(session, DUPLICATE_CODE)
    await session.refresh(employee)
    return employee


async def delete_employee(session: AsyncSession, employee_id: int) -> None:
    employee = await get_employee(session, employee_id)
    await session.delete(employee)
    await session.commit()
