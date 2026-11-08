import asyncio
import hashlib
from collections.abc import AsyncIterator

from shiftopt.constraints.labor_law_vn import LaborRules
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import commit_unique
from src.demand.csv_import import parse_demand_csv
from src.demand.models import DemandProfile, DemandSource, StaffingMode
from src.demand.sales_ingest import derive_demand, inspect_sales
from src.demand.schemas import (
    ConversionParams,
    CsvDemandRequest,
    DemandProfileCreate,
    DemandProfileUpdate,
    SalesIngestQuery,
    SalesInspection,
    SalesMapping,
)
from src.exceptions import InvalidInputError, NotFoundError, UploadTooLargeError

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


async def read_upload(chunks: AsyncIterator[bytes], limit: int) -> bytearray:
    """Collect an uploaded body, refusing it as soon as it grows past limit bytes."""
    data = bytearray()
    async for chunk in chunks:
        data.extend(chunk)
        if len(data) > limit:
            raise UploadTooLargeError(f"file must be at most {limit} bytes")
    if not data:
        raise InvalidInputError("file is empty")
    return data


async def inspect_upload(data: bytearray) -> SalesInspection:
    return await asyncio.to_thread(inspect_sales, bytes(data))


async def ingest_sales(
    session: AsyncSession, query: SalesIngestQuery, data: bytearray
) -> DemandProfile:
    """Derive a profile from an uploaded sales file. The stored profile keeps the weekly load, so
    the staffing sweep can re-derive head counts later without the file. The SHA-256 of the file
    and the mapping used are recorded in the metadata."""
    mapping = SalesMapping.model_validate(query.model_dump())
    conversion = ConversionParams.model_validate(query.model_dump())
    digest = hashlib.sha256(data).hexdigest()
    demand = await asyncio.to_thread(
        derive_demand, bytes(data), mapping, conversion, LaborRules(), digest
    )
    profile = DemandProfile(
        name=query.name,
        source=DemandSource.SALES,
        mode=StaffingMode.LINEAR,
        required_staff=list(demand.required_staff),
        conversion_params=conversion.model_dump(),
        source_metadata=demand.metadata,
        sales_load=list(demand.load),
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
