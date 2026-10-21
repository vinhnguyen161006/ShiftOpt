from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.analysis.router import router as analysis_router
from src.config import get_settings
from src.database import create_engine, create_session_factory
from src.demand.router import router as demand_router
from src.employees.router import router as employees_router
from src.exceptions import register_exception_handlers
from src.schedules.router import router as schedules_router
from src.shifts.router import router as shifts_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """TODO: on startup mark solve runs left in status running as failed (see
    schedules.service.recover_stale_runs) and stop accepting new runs while recovering."""
    engine = create_engine(get_settings().database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ShiftOpt", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    for router in (
        demand_router,
        employees_router,
        shifts_router,
        schedules_router,
        analysis_router,
    ):
        app.include_router(router, prefix="/api")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
