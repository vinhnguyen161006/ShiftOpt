from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schedules import service
from src.schedules.models import SolveRun

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def valid_run(run_id: int, session: SessionDep) -> SolveRun:
    return await service.get_run(session, run_id)


ValidRun = Annotated[SolveRun, Depends(valid_run)]
