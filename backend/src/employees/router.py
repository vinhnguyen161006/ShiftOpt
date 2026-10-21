from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.employees import service
from src.employees.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["employees"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[EmployeeRead])
async def list_employees(session: SessionDep) -> list[EmployeeRead]:
    return [EmployeeRead.model_validate(e) for e in await service.list_employees(session)]


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(payload: EmployeeCreate, session: SessionDep) -> EmployeeRead:
    return EmployeeRead.model_validate(await service.create_employee(session, payload))


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(employee_id: int, session: SessionDep) -> EmployeeRead:
    return EmployeeRead.model_validate(await service.get_employee(session, employee_id))


@router.put("/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int, payload: EmployeeUpdate, session: SessionDep
) -> EmployeeRead:
    return EmployeeRead.model_validate(await service.update_employee(session, employee_id, payload))


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: int, session: SessionDep) -> Response:
    await service.delete_employee(session, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
