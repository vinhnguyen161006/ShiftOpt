from sqlalchemy.ext.asyncio import AsyncSession

from src.employees.models import EmployeeRecord
from src.employees.schemas import EmployeeCreate, EmployeeUpdate


async def list_employees(session: AsyncSession) -> list[EmployeeRecord]:
    """TODO: return every employee ordered by code."""
    raise NotImplementedError


async def get_employee(session: AsyncSession, employee_id: int) -> EmployeeRecord:
    """TODO: return one employee or raise NotFoundError."""
    raise NotImplementedError


async def create_employee(session: AsyncSession, payload: EmployeeCreate) -> EmployeeRecord:
    """TODO: persist; reject a duplicate code with ConflictError and enforce
    Settings.max_employees with InstanceTooLargeError."""
    raise NotImplementedError


async def update_employee(
    session: AsyncSession, employee_id: int, payload: EmployeeUpdate
) -> EmployeeRecord:
    """TODO: replace the employee fields."""
    raise NotImplementedError


async def delete_employee(session: AsyncSession, employee_id: int) -> None:
    """TODO: delete the employee; saved schedules keep their instance snapshot."""
    raise NotImplementedError
