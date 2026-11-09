import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.models import AnalysisKind, AnalysisRun
from src.analysis.schemas import (
    BaselineCompareRequest,
    DemandSweepRequest,
    FairnessSweepRequest,
    LpDualsRequest,
    MarginalCostRequest,
    StaffingSweepRequest,
)
from src.analysis.worker import run_analysis
from src.config import get_settings
from src.demand.service import get_profile
from src.exceptions import InvalidInputError, NotFoundError
from src.jobs import JOB_GRACE_SECONDS, JobContext, ensure_job_capacity, run_in_child
from src.schedules.models import RunStatus
from src.schedules.service import check_limits, snapshot_for, solve_params

logger = logging.getLogger(__name__)

AnalysisRequest = (
    DemandSweepRequest
    | MarginalCostRequest
    | LpDualsRequest
    | StaffingSweepRequest
    | FairnessSweepRequest
    | BaselineCompareRequest
)
STAFFING_FIELDS = ("alpha", "productivity", "min_staff", "night_min_staff")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def create_run(
    session: AsyncSession,
    owner_id: int,
    kind: AnalysisKind,
    request: AnalysisRequest,
) -> AnalysisRun:
    await ensure_job_capacity(session)
    check_limits(request.solve)
    body: dict[str, Any] = {
        "snapshot": await snapshot_for(session, owner_id, request.solve),
        "params": solve_params(request.solve),
    }
    if isinstance(request, DemandSweepRequest):
        body["multipliers"] = request.multipliers
    elif isinstance(request, StaffingSweepRequest):
        body.update(await _staffing_inputs(session, owner_id, request))
    elif isinstance(request, FairnessSweepRequest):
        body["tolerances"] = request.tolerances
    elif not isinstance(request, BaselineCompareRequest):
        body["hourly_wage"] = request.hourly_wage
    run = AnalysisRun(owner_id=owner_id, kind=kind, status=RunStatus.QUEUED, request=body)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def _staffing_inputs(
    session: AsyncSession, owner_id: int, request: StaffingSweepRequest
) -> dict[str, Any]:
    profile = await get_profile(session, owner_id, request.solve.demand_profile_id)
    if profile.sales_load is None:
        raise InvalidInputError(
            "staffing sweep needs a demand profile built from a sales file; "
            "create the profile again by ingesting the file"
        )
    return {
        "assumption": request.assumption,
        "values": request.values,
        "load": list(profile.sales_load),
        "night_from_sales": profile.source_metadata.get("night_from_sales") == "True",
        "base": {field: profile.conversion_params[field] for field in STAFFING_FIELDS},
    }


async def execute_run(jobs: JobContext, run_id: int) -> None:
    async with jobs.session_factory() as session:
        run = await session.get(AnalysisRun, run_id)
        if run is None or run.status is not RunStatus.QUEUED:
            return
        run.status = RunStatus.RUNNING
        await session.commit()
        kind = run.kind
        request = run.request
    timeout = get_settings().max_analysis_seconds + JOB_GRACE_SECONDS
    try:
        result = await run_in_child(jobs, run_analysis, kind.value, request, limit_seconds=timeout)
    except TimeoutError:
        await _finish(jobs, run_id, _failure("analysis exceeded its time limit"))
        return
    except ValueError as error:
        await _finish(jobs, run_id, _failure(str(error)))
        return
    except Exception:
        logger.exception("analysis run %s crashed", run_id)
        await _finish(jobs, run_id, _failure("internal error"))
        return
    await _finish(
        jobs,
        run_id,
        {"status": RunStatus.SUCCEEDED, "result": result, "error": None, "finished_at": _utc_now()},
    )


def _failure(error: str) -> dict[str, Any]:
    return {"status": RunStatus.FAILED, "error": error, "finished_at": _utc_now()}


async def _finish(jobs: JobContext, run_id: int, fields: dict[str, Any]) -> None:
    async with jobs.session_factory() as session:
        run = await session.get(AnalysisRun, run_id)
        if run is None:
            return
        for name, value in fields.items():
            setattr(run, name, value)
        await session.commit()


async def get_run(session: AsyncSession, owner_id: int, run_id: int) -> AnalysisRun:
    run = await session.get(AnalysisRun, run_id)
    if run is None or run.owner_id != owner_id:
        raise NotFoundError(f"analysis run {run_id} not found")
    return run


async def recover_stale_runs(session: AsyncSession) -> int:
    stale = list(
        await session.scalars(
            select(AnalysisRun).where(AnalysisRun.status.in_([RunStatus.QUEUED, RunStatus.RUNNING]))
        )
    )
    for run in stale:
        run.status = RunStatus.FAILED
        run.error = "server restarted"
        run.finished_at = _utc_now()
    await session.commit()
    return len(stale)
