from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUserDep
from src.config import get_settings
from src.database import get_session
from src.demand import service
from src.demand.schemas import (
    CsvDemandRequest,
    DemandProfileCreate,
    DemandProfileRead,
    DemandProfileUpdate,
    SalesIngestQuery,
    SalesInspection,
)

router = APIRouter(prefix="/demand-profiles", tags=["demand"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[DemandProfileRead])
async def list_profiles(session: SessionDep, user: CurrentUserDep) -> list[DemandProfileRead]:
    return [
        DemandProfileRead.model_validate(p) for p in await service.list_profiles(session, user.id)
    ]


@router.post("", response_model=DemandProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: DemandProfileCreate, session: SessionDep, user: CurrentUserDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(await service.create_profile(session, user.id, payload))


BINARY_BODY = {
    "requestBody": {
        "required": True,
        "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
    }
}


@router.post("/ingest/inspect", response_model=SalesInspection, openapi_extra=BINARY_BODY)
async def inspect_sales_upload(request: Request) -> SalesInspection:
    data = await service.read_upload(request.stream(), get_settings().max_upload_bytes)
    return await service.inspect_upload(data)


@router.post(
    "/ingest",
    response_model=DemandProfileRead,
    status_code=status.HTTP_201_CREATED,
    openapi_extra=BINARY_BODY,
)
async def ingest_sales(
    query: Annotated[SalesIngestQuery, Query()],
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> DemandProfileRead:
    data = await service.read_upload(request.stream(), get_settings().max_upload_bytes)
    return DemandProfileRead.model_validate(
        await service.ingest_sales(session, user.id, query, data)
    )


@router.post("/from-csv", response_model=DemandProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile_from_csv(
    payload: CsvDemandRequest, session: SessionDep, user: CurrentUserDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(
        await service.create_profile_from_csv(session, user.id, payload)
    )


@router.get("/{profile_id}", response_model=DemandProfileRead)
async def get_profile(
    profile_id: int, session: SessionDep, user: CurrentUserDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(await service.get_profile(session, user.id, profile_id))


@router.put("/{profile_id}", response_model=DemandProfileRead)
async def update_profile(
    profile_id: int, payload: DemandProfileUpdate, session: SessionDep, user: CurrentUserDep
) -> DemandProfileRead:
    return DemandProfileRead.model_validate(
        await service.update_profile(session, user.id, profile_id, payload)
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: int, session: SessionDep, user: CurrentUserDep) -> Response:
    await service.delete_profile(session, user.id, profile_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
