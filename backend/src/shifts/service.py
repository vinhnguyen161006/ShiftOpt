from shiftopt.constraints.labor_law_vn import LaborRules
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import commit_unique
from src.exceptions import InvalidInputError, NotFoundError
from src.shifts.models import ShiftTemplate
from src.shifts.schemas import ShiftTemplateCreate, ShiftTemplateUpdate

DUPLICATE_NAME = "shift template name already exists"


def _check_length(length_hours: int) -> None:
    limit = LaborRules().max_daily_hours
    if length_hours > limit:
        raise InvalidInputError(f"shift length must not exceed {limit} hours (Article 105)")


async def list_templates(session: AsyncSession) -> list[ShiftTemplate]:
    result = await session.scalars(
        select(ShiftTemplate).order_by(ShiftTemplate.start_hour, ShiftTemplate.name)
    )
    return list(result)


async def get_template(session: AsyncSession, template_id: int) -> ShiftTemplate:
    template = await session.get(ShiftTemplate, template_id)
    if template is None:
        raise NotFoundError(f"shift template {template_id} not found")
    return template


async def create_template(session: AsyncSession, payload: ShiftTemplateCreate) -> ShiftTemplate:
    _check_length(payload.length_hours)
    template = ShiftTemplate(**payload.model_dump())
    session.add(template)
    await commit_unique(session, DUPLICATE_NAME)
    await session.refresh(template)
    return template


async def update_template(
    session: AsyncSession, template_id: int, payload: ShiftTemplateUpdate
) -> ShiftTemplate:
    _check_length(payload.length_hours)
    template = await get_template(session, template_id)
    for field, value in payload.model_dump().items():
        setattr(template, field, value)
    await commit_unique(session, DUPLICATE_NAME)
    await session.refresh(template)
    return template


async def delete_template(session: AsyncSession, template_id: int) -> None:
    template = await get_template(session, template_id)
    await session.delete(template)
    await session.commit()
