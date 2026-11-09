import os
from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src import main
from src.auth.dependencies import current_user
from src.auth.models import UserRecord
from src.main import create_app

STUB_USER = UserRecord(id=1, email="stub@example.com", password_hash=None, display_name="stub")


@pytest.fixture
async def app(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FastAPI]:
    async def skip_recovery(session_factory: object) -> None:
        return None

    monkeypatch.setattr(main, "recover_interrupted_jobs", skip_recovery)
    application = create_app()
    application.dependency_overrides[current_user] = lambda: STUB_USER
    async with LifespanManager(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.fixture
def database_url() -> str:
    url = os.environ.get("SHIFTOPT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SHIFTOPT_TEST_DATABASE_URL is not set")
    return url
