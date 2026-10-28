import asyncio
from pathlib import Path

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.call_arrivals import simulate_arrival_rates
from shiftopt.staffing.erlang import required_staff_erlang_a
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import commit_unique
from src.demand.csv_import import parse_demand_csv
from src.demand.dataset_loader import dataset_required_staff
from src.demand.models import DemandProfile, DemandSource, StaffingMode
from src.demand.schemas import (
    CallCenterDemandRequest,
    CsvDemandRequest,
    DatasetDemandRequest,
    DemandProfileCreate,
    DemandProfileUpdate,
)
from src.exceptions import InvalidInputError, NotFoundError

DUPLICATE_NAME = "demand profile name already exists"


async def list_profiles(session: AsyncSession) -> list[DemandProfile]:
    result = await session.scalars(
        select(DemandProfile).order_by(DemandProfile.created_at.desc(), DemandProfile.id.desc())
    )
    return list(result)


async def get_profile(session: AsyncSession, profile_id: int) -> DemandProfile:
    profile = await session.get(DemandProfile, profile_id)
    if profile is None:
        raise NotFoundError(f"demand profile {profile_id} not found")
    return profile


async def _persist(session: AsyncSession, profile: DemandProfile) -> DemandProfile:
    session.add(profile)
    await commit_unique(session, DUPLICATE_NAME)
    await session.refresh(profile)
    return profile


async def create_profile(session: AsyncSession, payload: DemandProfileCreate) -> DemandProfile:
    profile = DemandProfile(
        **payload.model_dump(),
        source_metadata={},
    )
    return await _persist(session, profile)


async def update_profile(
    session: AsyncSession, profile_id: int, payload: DemandProfileUpdate
) -> DemandProfile:
    profile = await get_profile(session, profile_id)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    await commit_unique(session, DUPLICATE_NAME)
    await session.refresh(profile)
    return profile


async def delete_profile(session: AsyncSession, profile_id: int) -> None:
    profile = await get_profile(session, profile_id)
    await session.delete(profile)
    await session.commit()


async def create_profile_from_dataset(
    session: AsyncSession, payload: DatasetDemandRequest
) -> DemandProfile:
    demand = await asyncio.to_thread(
        dataset_required_staff,
        Path(get_settings().dataset_dir),
        payload.store_id,
        payload.conversion_params,
        LaborRules(),
    )
    profile = DemandProfile(
        name=payload.name,
        source=DemandSource.FRESHRETAILNET,
        mode=StaffingMode.LINEAR,
        required_staff=list(demand.required_staff),
        conversion_params=payload.conversion_params.model_dump(),
        source_metadata=demand.metadata,
    )
    return await _persist(session, profile)


async def create_profile_from_csv(
    session: AsyncSession, payload: CsvDemandRequest
) -> DemandProfile:
    try:
        required = parse_demand_csv(payload.csv_text)
    except ValueError as error:
        raise InvalidInputError(str(error)) from error
    profile = DemandProfile(
        name=payload.name,
        source=DemandSource.CSV,
        mode=StaffingMode.LINEAR,
        required_staff=required,
        conversion_params={},
        source_metadata={"method": "head counts typed in a CSV file"},
    )
    return await _persist(session, profile)


async def create_profile_from_call_center(
    session: AsyncSession, payload: CallCenterDemandRequest
) -> DemandProfile:
    required = await asyncio.to_thread(_call_center_staff, payload)
    profile = DemandProfile(
        name=payload.name,
        source=DemandSource.CALL_CENTER,
        mode=StaffingMode.ERLANG,
        required_staff=list(required),
        conversion_params=payload.model_dump(exclude={"name"}),
        source_metadata={
            "method": "Erlang A on simulated hourly arrival rates",
            "label": "simulated call arrivals with a fixed seed; not observed call data",
            "seed": str(payload.seed),
        },
    )
    return await _persist(session, profile)


def _call_center_staff(payload: CallCenterDemandRequest) -> tuple[int, ...]:
    try:
        rates = simulate_arrival_rates(payload.base_rate, noise=payload.noise, seed=payload.seed)
        return required_staff_erlang_a(
            rates,
            handle_seconds=payload.handle_seconds,
            patience_seconds=payload.patience_seconds,
            target_service_level=payload.service_level,
            answer_seconds=payload.answer_seconds,
            min_staff=payload.min_staff,
        )
    except ValueError as error:
        raise InvalidInputError(str(error)) from error
