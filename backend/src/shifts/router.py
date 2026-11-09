from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUserDep
from src.database import get_session
from src.shifts import service
from src.shifts.schemas import ShiftTemplateCreate, ShiftTemplateRead, ShiftTemplateUpdate

router = APIRouter(prefix="/shift-templates", tags=["shifts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[ShiftTemplateRead])
async def list_templates(session: SessionDep, user: CurrentUserDep) -> list[ShiftTemplateRead]:
    return [
        ShiftTemplateRead.model_validate(t) for t in await service.list_templates(session, user.id)
    ]


@router.post("", response_model=ShiftTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: ShiftTemplateCreate, session: SessionDep, user: CurrentUserDep
) -> ShiftTemplateRead:
    return ShiftTemplateRead.model_validate(
        await service.create_template(session, user.id, payload)
    )


@router.get("/{template_id}", response_model=ShiftTemplateRead)
async def get_template(
    template_id: int, session: SessionDep, user: CurrentUserDep
) -> ShiftTemplateRead:
    return ShiftTemplateRead.model_validate(
        await service.get_template(session, user.id, template_id)
    )


@router.put("/{template_id}", response_model=ShiftTemplateRead)
async def update_template(
    template_id: int, payload: ShiftTemplateUpdate, session: SessionDep, user: CurrentUserDep
) -> ShiftTemplateRead:
    return ShiftTemplateRead.model_validate(
        await service.update_template(session, user.id, template_id, payload)
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, session: SessionDep, user: CurrentUserDep) -> Response:
    await service.delete_template(session, user.id, template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
