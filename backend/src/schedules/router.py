from fastapi import APIRouter, BackgroundTasks, Query, Response, status

from src.jobs import JobsDep
from src.schedules import service
from src.schedules.dependencies import SessionDep, ValidRun
from src.schedules.schemas import (
    ComplianceRead,
    JobAccepted,
    KpiRead,
    ManualEditRequest,
    RepairRequest,
    ReplacementRead,
    RerosterRequest,
    ScheduleChangesRead,
    SolveRequest,
    SolveRunRead,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])

CSV_MEDIA_TYPE = "text/csv"


def _csv_response(content: str, run_id: int, name: str) -> Response:
    return Response(
        content=content,
        media_type=CSV_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="run-{run_id}-{name}.csv"'},
    )


@router.post("", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_schedule(
    payload: SolveRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> JobAccepted:
    run = await service.create_run(session, payload)
    background.add_task(service.execute_run, jobs, run.id)
    return JobAccepted(job_id=run.id, status=run.status)


@router.get("", response_model=list[SolveRunRead])
async def list_schedules(session: SessionDep) -> list[SolveRunRead]:
    return [SolveRunRead.model_validate(r) for r in await service.list_runs(session)]


@router.get("/{run_id}", response_model=SolveRunRead)
async def get_schedule(run: ValidRun) -> SolveRunRead:
    return SolveRunRead.model_validate(run)


@router.get("/{run_id}/compliance", response_model=ComplianceRead)
async def get_schedule_compliance(run: ValidRun) -> ComplianceRead:
    return service.get_compliance(run)


@router.get("/{run_id}/kpi", response_model=KpiRead)
async def get_schedule_kpi(run: ValidRun) -> KpiRead:
    return service.get_kpi(run)


@router.get("/{run_id}/assignments.csv")
async def get_assignments_csv(run: ValidRun) -> Response:
    return _csv_response(service.assignments_csv(run), run.id, "assignments")


@router.get("/{run_id}/coverage.csv")
async def get_coverage_csv(run: ValidRun) -> Response:
    return _csv_response(service.coverage_csv(run), run.id, "coverage")


@router.get("/{run_id}/kpi.csv")
async def get_kpi_csv(run: ValidRun) -> Response:
    return _csv_response(service.kpi_csv(service.get_kpi(run)), run.id, "kpi")


@router.post("/{run_id}/edits", response_model=SolveRunRead, status_code=status.HTTP_201_CREATED)
async def create_manual_edit(
    run: ValidRun, payload: ManualEditRequest, session: SessionDep
) -> SolveRunRead:
    edited = await service.create_manual_edit(session, run, payload)
    return SolveRunRead.model_validate(edited)


@router.post("/{run_id}/repair", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_repair(
    run: ValidRun,
    payload: RepairRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> JobAccepted:
    repaired = await service.create_repair_run(session, run, payload)
    background.add_task(service.execute_run, jobs, repaired.id)
    return JobAccepted(job_id=repaired.id, status=repaired.status)


@router.get("/{run_id}/replacements", response_model=list[ReplacementRead])
async def get_replacements(
    run: ValidRun,
    employee_code: str = Query(min_length=1, max_length=32),
    day: int = Query(ge=0, le=6),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[ReplacementRead]:
    return service.get_replacements(run, employee_code, day, limit)


@router.post("/{run_id}/reroster", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_reroster(
    run: ValidRun,
    payload: RerosterRequest,
    session: SessionDep,
    jobs: JobsDep,
    background: BackgroundTasks,
) -> JobAccepted:
    queued = await service.create_reroster(session, run, payload)
    background.add_task(service.execute_run, jobs, queued.id)
    return JobAccepted(job_id=queued.id, status=queued.status)


@router.get("/{run_id}/changes", response_model=ScheduleChangesRead)
async def get_schedule_changes(run: ValidRun, session: SessionDep) -> ScheduleChangesRead:
    return await service.changes_for(session, run)
