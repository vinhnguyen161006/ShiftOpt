from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis import service
from src.analysis.models import AnalysisKind
from src.analysis.schemas import (
    AnalysisAccepted,
    AnalysisRunRead,
    DemandSweepRequest,
    LpDualsRequest,
    MarginalCostRequest,
)
from src.analysis.service import AnalysisRequest
from src.database import get_session
from src.jobs import JobContext, JobsDep

router = APIRouter(prefix="/analysis", tags=["analysis"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _accept(
    session: AsyncSession,
    jobs: JobContext,
    background: BackgroundTasks,
    kind: AnalysisKind,
    request: AnalysisRequest,
) -> AnalysisAccepted:
    run = await service.create_run(session, kind, request)
    background.add_task(service.execute_run, jobs, run.id)
    return AnalysisAccepted(job_id=run.id, status=run.status)


@router.post("/demand-sweep", response_model=AnalysisAccepted, status_code=status.HTTP_202_ACCEPTED)
async def demand_sweep(
    payload: DemandSweepRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> AnalysisAccepted:
    return await _accept(session, jobs, background, AnalysisKind.DEMAND_SWEEP, payload)


@router.post(
    "/marginal-cost", response_model=AnalysisAccepted, status_code=status.HTTP_202_ACCEPTED
)
async def marginal_cost(
    payload: MarginalCostRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> AnalysisAccepted:
    return await _accept(session, jobs, background, AnalysisKind.MARGINAL_COST, payload)


@router.post("/lp-duals", response_model=AnalysisAccepted, status_code=status.HTTP_202_ACCEPTED)
async def lp_duals(
    payload: LpDualsRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> AnalysisAccepted:
    return await _accept(session, jobs, background, AnalysisKind.LP_DUALS, payload)


@router.get("/{run_id}", response_model=AnalysisRunRead)
async def get_analysis(run_id: int, session: SessionDep) -> AnalysisRunRead:
    return AnalysisRunRead.model_validate(await service.get_run(session, run_id))
