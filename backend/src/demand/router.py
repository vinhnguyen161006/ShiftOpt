from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.demand import service
from src.demand.schemas import (
    DatasetDemandRequest,
    DemandProfileCreate,
    DemandProfileRead,
    DemandProfileUpdate,
)

router = APIRouter(prefix="/demand-profiles", tags=["demand"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[DemandProfileRead])
async def list_profiles(session: SessionDep) -> list[DemandProfileRead]:
    return [DemandProfileRead.model_validate(p) for p in await service.list_profiles(session)]


@router.post("", response_model=DemandProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(payload: DemandProfileCreate, session: SessionDep) -> DemandProfileRead:
    return DemandProfileRead.model_validate(await service.create_profile(session, payload))


@router.post("/from-dataset", response_model=DemandProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile_from_dataset(
    payload: DatasetDemandRequest, session: SessionDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(
        await service.create_profile_from_dataset(session, payload)
    )


@router.get("/{profile_id}", response_model=DemandProfileRead)
async def get_profile(profile_id: int, session: SessionDep) -> DemandProfileRead:
    return DemandProfileRead.model_validate(await service.get_profile(session, profile_id))


@router.put("/{profile_id}", response_model=DemandProfileRead)
async def update_profile(
    profile_id: int, payload: DemandProfileUpdate, session: SessionDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(
        await service.update_profile(session, profile_id, payload)
    )
