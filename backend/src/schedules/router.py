from fastapi import APIRouter, BackgroundTasks, status

from src.schedules import service
from src.schedules.dependencies import SessionDep, ValidRun
from src.schedules.schemas import ComplianceRead, JobAccepted, KpiRead, SolveRequest, SolveRunRead

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_schedule(
    payload: SolveRequest, session: SessionDep, background: BackgroundTasks
) -> JobAccepted:
    run = await service.create_run(session, payload)
    background.add_task(service.execute_run, run.id)
    return JobAccepted(job_id=run.id, status=run.status)


@router.get("", response_model=list[SolveRunRead])
async def list_schedules(session: SessionDep) -> list[SolveRunRead]:
    return [SolveRunRead.model_validate(r) for r in await service.list_runs(session)]


@router.get("/{run_id}", response_model=SolveRunRead)
async def get_schedule(run: ValidRun) -> SolveRunRead:
    return SolveRunRead.model_validate(run)


@router.get("/{run_id}/compliance", response_model=ComplianceRead)
async def get_schedule_compliance(run: ValidRun, session: SessionDep) -> ComplianceRead:
    return await service.get_compliance(session, run.id)


@router.get("/{run_id}/kpi", response_model=KpiRead)
async def get_schedule_kpi(run: ValidRun, session: SessionDep) -> KpiRead:
    return await service.get_kpi(session, run.id)
