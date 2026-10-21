from sqlalchemy.ext.asyncio import AsyncSession

from src.demand.models import DemandProfile
from src.demand.schemas import DatasetDemandRequest, DemandProfileCreate, DemandProfileUpdate


async def list_profiles(session: AsyncSession) -> list[DemandProfile]:
    """TODO: return every demand profile, newest first."""
    raise NotImplementedError


async def get_profile(session: AsyncSession, profile_id: int) -> DemandProfile:
    """TODO: return one profile or raise NotFoundError."""
    raise NotImplementedError


async def create_profile(session: AsyncSession, payload: DemandProfileCreate) -> DemandProfile:
    """TODO: validate non-negative head counts and a unique name, then persist."""
    raise NotImplementedError


async def update_profile(
    session: AsyncSession, profile_id: int, payload: DemandProfileUpdate
) -> DemandProfile:
    """TODO: replace the profile; saved schedules keep their own instance snapshot."""
    raise NotImplementedError


async def create_profile_from_dataset(
    session: AsyncSession, payload: DatasetDemandRequest
) -> DemandProfile:
    """TODO: build required_staff for one FreshRetailNet store via dataset_loader and
    shiftopt.staffing.linear, record alpha and productivity in conversion_params."""
    raise NotImplementedError
