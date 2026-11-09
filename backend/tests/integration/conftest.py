from collections.abc import AsyncIterator
from typing import Any

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.auth.dependencies import current_user
from src.auth.models import UserRecord
from src.config import get_settings
from src.main import create_app
from tests.integration.helpers import DAY_DEMAND

TABLES = (
    "auth_sessions",
    "users",
    "analysis_runs",
    "solve_runs",
    "demand_profiles",
    "employees",
    "shift_templates",
)
STUB_USER = UserRecord(id=1, email="stub@example.com", password_hash=None, display_name="stub")


@pytest.fixture
async def app(database_url: str, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FastAPI]:
    monkeypatch.setenv("SHIFTOPT_DATABASE_URL", database_url)
    get_settings.cache_clear()
    application = create_app()
    application.dependency_overrides[current_user] = lambda: STUB_USER
    async with LifespanManager(application):
        async with application.state.engine.begin() as connection:
            for table in TABLES:
                await connection.execute(text(f"DELETE FROM {table}"))
            await connection.execute(
                text("INSERT INTO users (id, email, display_name) VALUES (:id, :email, :name)"),
                {"id": STUB_USER.id, "email": STUB_USER.email, "name": STUB_USER.display_name},
            )
        yield application
    get_settings.cache_clear()


@pytest.fixture
async def anonymous_client(
    database_url: str, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setenv("SHIFTOPT_DATABASE_URL", database_url)
    monkeypatch.setenv("SHIFTOPT_ALLOWED_EMAILS", '["ada@example.com"]')
    get_settings.cache_clear()
    application = create_app()
    async with LifespanManager(application):
        async with application.state.engine.begin() as connection:
            for table in TABLES:
                await connection.execute(text(f"DELETE FROM {table}"))
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test"
        ) as http:
            yield http
    get_settings.cache_clear()


@pytest.fixture
async def seeded(client: AsyncClient) -> dict[str, Any]:
    profile = await client.post(
        "/api/demand-profiles", json={"name": "week", "required_staff": DAY_DEMAND}
    )
    shift_ids = []
    for name, start in (("day", 8), ("evening", 14), ("morning", 6)):
        template = await client.post(
            "/api/shift-templates",
            json={"name": name, "start_hour": start, "length_hours": 8},
        )
        shift_ids.append(template.json()["id"])
    for code in ("E1", "E2", "E3", "E4"):
        await client.post("/api/employees", json={"code": code, "name": code, "hourly_wage": 100})
    return {"profile_id": profile.json()["id"], "shift_ids": shift_ids}
