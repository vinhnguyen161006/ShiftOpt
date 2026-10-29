from collections.abc import AsyncIterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analysis import service as analysis_service
from src.analysis.router import router as analysis_router
from src.config import get_settings
from src.database import create_engine, create_session_factory
from src.demand.router import router as demand_router
from src.employees.router import router as employees_router
from src.exceptions import register_exception_handlers
from src.jobs import JobContext
from src.rules.router import router as rules_router
from src.schedules import service as schedules_service
from src.schedules.router import router as schedules_router
from src.shifts.router import router as shifts_router


async def recover_interrupted_jobs(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        await schedules_service.recover_stale_runs(session)
        await analysis_service.recover_stale_runs(session)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    executor = ProcessPoolExecutor(max_workers=settings.max_concurrent_jobs)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.jobs = JobContext(session_factory, executor)
    await recover_interrupted_jobs(session_factory)
    yield
    executor.shutdown(wait=False, cancel_futures=True)
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ShiftOpt", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_exception_handlers(app)
    for router in (
        demand_router,
        employees_router,
        shifts_router,
        schedules_router,
        analysis_router,
        rules_router,
    ):
        app.include_router(router, prefix="/api")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
