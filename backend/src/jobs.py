import asyncio
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

JOB_GRACE_SECONDS = 30.0


@dataclass(frozen=True)
class JobContext:
    session_factory: async_sessionmaker[AsyncSession]
    executor: ProcessPoolExecutor


def get_jobs(request: Request) -> JobContext:
    jobs: JobContext = request.app.state.jobs
    return jobs


JobsDep = Annotated[JobContext, Depends(get_jobs)]


async def run_in_child(
    jobs: JobContext,
    function: Callable[..., dict[str, Any]],
    *args: Any,
    limit_seconds: float,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    async with asyncio.timeout(limit_seconds):
        return await loop.run_in_executor(jobs.executor, function, *args)
