from collections.abc import AsyncIterator
from typing import Any

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text

from src.config import get_settings
from src.main import create_app
from tests.integration.helpers import DAY_DEMAND

TABLES = ("analysis_runs", "solve_runs", "demand_profiles", "employees", "shift_templates")


@pytest.fixture
async def app(database_url: str, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[FastAPI]:
    monkeypatch.setenv("SHIFTOPT_DATABASE_URL", database_url)
    get_settings.cache_clear()
    application = create_app()
    async with LifespanManager(application):
        async with application.state.engine.begin() as connection:
            for table in TABLES:
                await connection.execute(text(f"DELETE FROM {table}"))
        yield application
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
