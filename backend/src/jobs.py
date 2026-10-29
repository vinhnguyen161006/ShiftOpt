import asyncio
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analysis.models import AnalysisRun
from src.config import get_settings
from src.exceptions import TooManyJobsError
from src.schedules.models import RunStatus, SolveRun

JOB_GRACE_SECONDS = 30.0
ACTIVE_STATUSES = (RunStatus.QUEUED, RunStatus.RUNNING)


@dataclass(frozen=True)
class JobContext:
    session_factory: async_sessionmaker[AsyncSession]
    executor: ProcessPoolExecutor


def get_jobs(request: Request) -> JobContext:
    jobs: JobContext = request.app.state.jobs
    return jobs


JobsDep = Annotated[JobContext, Depends(get_jobs)]


async def count_active_jobs(session: AsyncSession) -> int:
    total = 0
    for model in (SolveRun, AnalysisRun):
        count = await session.scalar(
            select(func.count()).select_from(model).where(model.status.in_(ACTIVE_STATUSES))
        )
        total += count or 0
    return total


async def ensure_job_capacity(session: AsyncSession) -> None:
    if await count_active_jobs(session) >= get_settings().max_pending_jobs:
        raise TooManyJobsError("too many solve jobs in progress, retry later")


async def run_in_child(
    jobs: JobContext,
    function: Callable[..., dict[str, Any]],
    *args: Any,
    limit_seconds: float,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    async with asyncio.timeout(limit_seconds):
        return await loop.run_in_executor(jobs.executor, function, *args)
