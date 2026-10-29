from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import update

from src.analysis.models import AnalysisKind, AnalysisRun
from src.main import recover_interrupted_jobs
from src.schedules.models import RunStatus, SolveRun
from tests.integration.helpers import solve_body

pytestmark = pytest.mark.integration

MAX_PENDING = 4


async def _insert_jobs(app: FastAPI, status: RunStatus, count: int) -> None:
    async with app.state.session_factory() as session:
        for _ in range(count):
            session.add(SolveRun(status=status, params={}, instance_snapshot={}))
        await session.commit()


async def _insert_analysis(app: FastAPI, status: RunStatus, count: int) -> None:
    async with app.state.session_factory() as session:
        for _ in range(count):
            session.add(AnalysisRun(kind=AnalysisKind.DEMAND_SWEEP, status=status, request={}))
        await session.commit()


async def _set_all_status(app: FastAPI, status: RunStatus) -> None:
    async with app.state.session_factory() as session:
        await session.execute(update(SolveRun).values(status=status))
        await session.execute(update(AnalysisRun).values(status=status))
        await session.commit()


async def test_schedule_refused_with_429_when_pending_jobs_are_full(
    app: FastAPI, client: AsyncClient, seeded: dict[str, Any]
) -> None:
    await _insert_jobs(app, RunStatus.RUNNING, 2)
    await _insert_analysis(app, RunStatus.QUEUED, MAX_PENDING - 2)

    refused = await client.post("/api/schedules", json=solve_body(seeded))

    assert refused.status_code == 429
    assert refused.json() == {"detail": "too many solve jobs in progress, retry later"}


async def test_analysis_refused_with_429_when_pending_jobs_are_full(
    app: FastAPI, client: AsyncClient, seeded: dict[str, Any]
) -> None:
    await _insert_jobs(app, RunStatus.QUEUED, MAX_PENDING)

    refused = await client.post(
        "/api/analysis/demand-sweep",
        json={"solve": solve_body(seeded), "multipliers": [1.0]},
    )

    assert refused.status_code == 429


async def test_finished_runs_do_not_count_toward_the_limit(
    app: FastAPI, client: AsyncClient, seeded: dict[str, Any]
) -> None:
    await _insert_jobs(app, RunStatus.SUCCEEDED, MAX_PENDING)
    await _insert_jobs(app, RunStatus.FAILED, MAX_PENDING)

    accepted = await client.post("/api/schedules", json=solve_body(seeded))

    assert accepted.status_code == 202


async def test_restart_releases_slots_taken_by_interrupted_jobs(
    app: FastAPI, client: AsyncClient, seeded: dict[str, Any]
) -> None:
    await _insert_jobs(app, RunStatus.RUNNING, MAX_PENDING)
    assert (await client.post("/api/schedules", json=solve_body(seeded))).status_code == 429

    await recover_interrupted_jobs(app.state.session_factory)

    assert (await client.post("/api/schedules", json=solve_body(seeded))).status_code == 202
    await _set_all_status(app, RunStatus.FAILED)
