from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service
from src.auth.models import UserRecord
from src.database import get_session

SESSION_COOKIE = "shiftopt_session"

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def current_user(
    session: SessionDep,
    shiftopt_session: Annotated[str | None, Cookie()] = None,
) -> UserRecord:
    return await service.resolve_session(session, shiftopt_session)
