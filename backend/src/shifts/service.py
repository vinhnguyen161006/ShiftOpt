from sqlalchemy.ext.asyncio import AsyncSession

from src.shifts.models import ShiftTemplate
from src.shifts.schemas import ShiftTemplateCreate, ShiftTemplateUpdate


async def list_templates(session: AsyncSession) -> list[ShiftTemplate]:
    """TODO: return every shift template ordered by start hour."""
    raise NotImplementedError


async def get_template(session: AsyncSession, template_id: int) -> ShiftTemplate:
    """TODO: return one template or raise NotFoundError."""
    raise NotImplementedError


async def create_template(session: AsyncSession, payload: ShiftTemplateCreate) -> ShiftTemplate:
    """TODO: reject a duplicate name with ConflictError and a length above
    LaborRules.max_daily_hours."""
    raise NotImplementedError


async def update_template(
    session: AsyncSession, template_id: int, payload: ShiftTemplateUpdate
) -> ShiftTemplate:
    """TODO: replace the template fields."""
    raise NotImplementedError


async def delete_template(session: AsyncSession, template_id: int) -> None:
    """TODO: delete the template."""
    raise NotImplementedError
