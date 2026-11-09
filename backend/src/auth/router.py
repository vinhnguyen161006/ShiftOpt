import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service
from src.auth.dependencies import SESSION_COOKIE, CurrentUserDep
from src.auth.schemas import LoginRequest, RegisterRequest, UserRead
from src.config import get_settings
from src.database import get_session
from src.exceptions import AppError, ForbiddenError, ServiceUnavailableError

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, session: SessionDep) -> UserRead:
    user = await service.register(session, payload.email, payload.password, payload.display_name)
    set_session_cookie(response, await service.open_session(session, user))
    return UserRead.model_validate(user)


@router.post("/login", response_model=UserRead)
async def login(payload: LoginRequest, response: Response, session: SessionDep) -> UserRead:
    user = await service.authenticate(session, payload.email, payload.password)
    set_session_cookie(response, await service.open_session(session, user))
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session: SessionDep,
    shiftopt_session: Annotated[str | None, Cookie()] = None,
) -> Response:
    await service.close_session(session, shiftopt_session)
    result = Response(status_code=status.HTTP_204_NO_CONTENT)
    result.delete_cookie(SESSION_COOKIE, path="/")
    return result


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(user)


def login_error_url(error: AppError) -> str:
    if isinstance(error, ServiceUnavailableError):
        code = "not_configured"
    elif isinstance(error, ForbiddenError):
        code = "not_allowed"
    else:
        code = "google_failed"
    return f"/login?error={code}"


@router.get("/google/start", include_in_schema=False)
async def google_start(session: SessionDep) -> RedirectResponse:
    try:
        target = await service.start_google_login(session)
    except AppError as error:
        return RedirectResponse(login_error_url(error), status_code=status.HTTP_302_FOUND)
    return RedirectResponse(target, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback", include_in_schema=False)
async def google_callback(
    session: SessionDep,
    state: Annotated[str | None, Query(max_length=128)] = None,
    code: Annotated[str | None, Query(max_length=2048)] = None,
    error: Annotated[str | None, Query(max_length=128)] = None,
) -> RedirectResponse:
    if error is not None or state is None or code is None:
        return RedirectResponse("/login?error=google_denied", status_code=status.HTTP_302_FOUND)
    try:
        user = await service.finish_google_login(session, code, state)
        token = await service.open_session(session, user)
    except AppError as failure:
        logger.warning("google sign-in stopped: %s (%s)", failure.message, type(failure).__name__)
        return RedirectResponse(login_error_url(failure), status_code=status.HTTP_302_FOUND)
    response = RedirectResponse(
        get_settings().post_login_redirect, status_code=status.HTTP_302_FOUND
    )
    set_session_cookie(response, token)
    return response
