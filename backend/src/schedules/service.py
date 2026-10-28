import csv
import io
import logging
from datetime import UTC, datetime
from typing import Any

from shiftopt import kpi
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Instance, Solution
from shiftopt.solvers.base import ModelInvalidError
from shiftopt.validation import LEGAL_BASIS, validate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.demand.service import get_profile
from src.employees.models import EmployeeRecord
from src.exceptions import ConflictError, InstanceTooLargeError, InvalidInputError, NotFoundError
from src.jobs import JOB_GRACE_SECONDS, JobContext, run_in_child
from src.schedules.models import RunStatus, SolveRun
from src.schedules.schemas import (
    ComplianceRead,
    KpiRead,
    ManualEditRequest,
    SolveRequest,
    ViolationRead,
)
from src.schedules.snapshot import (
    Snapshot,
    build_snapshot,
    instance_from_snapshot,
    solution_from_rows,
)
from src.schedules.worker import solve_snapshot
from src.shifts.models import ShiftTemplate

logger = logging.getLogger(__name__)

ASSIGNMENT_HEADER = [
    "employee_code",
    "day",
    "shift_name",
    "start_hour",
    "length_hours",
    "break_offset",
]
COVERAGE_HEADER = ["hour_of_week", "day", "hour", "required", "staffed"]
KPI_HEADER = ["metric", "value"]


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def solve_params(payload: SolveRequest) -> dict[str, float]:
    return {
        "time_limit_seconds": payload.time_limit_seconds,
        "relative_gap_limit": payload.relative_gap_limit,
        "num_workers": payload.num_workers,
        "random_seed": payload.random_seed,
    }


async def _templates(session: AsyncSession, ids: list[int]) -> list[ShiftTemplate]:
    found = list(await session.scalars(select(ShiftTemplate).where(ShiftTemplate.id.in_(ids))))
    missing = set(ids) - {template.id for template in found}
    if missing:
        raise NotFoundError(f"shift templates {sorted(missing)} not found")
    return found


async def _employees(session: AsyncSession, ids: list[int] | None) -> list[EmployeeRecord]:
    query = select(EmployeeRecord)
    if ids is not None:
        query = query.where(EmployeeRecord.id.in_(ids))
        found = list(await session.scalars(query))
        missing = set(ids) - {employee.id for employee in found}
        if missing:
            raise NotFoundError(f"employees {sorted(missing)} not found")
    else:
        found = list(await session.scalars(query))
    if not found:
        raise InvalidInputError("no employees to schedule")
    if len(found) > get_settings().max_employees:
        raise InstanceTooLargeError(
            f"at most {get_settings().max_employees} employees can be scheduled at once"
        )
    return found


def check_limits(payload: SolveRequest) -> None:
    settings = get_settings()
    if payload.time_limit_seconds > settings.max_solve_seconds:
        raise InstanceTooLargeError(
            f"time_limit_seconds must not exceed {settings.max_solve_seconds:g}"
        )
    if payload.num_workers > settings.solve_workers:
        raise InstanceTooLargeError(f"num_workers must not exceed {settings.solve_workers}")


async def snapshot_for(session: AsyncSession, payload: SolveRequest) -> Snapshot:
    check_limits(payload)
    profile = await get_profile(session, payload.demand_profile_id)
    templates = await _templates(session, payload.shift_template_ids)
    employees = await _employees(session, payload.employee_ids)
    rules = LaborRules(
        max_weekly_hours=payload.max_weekly_hours,
        max_consecutive_days=payload.max_consecutive_days,
    )
    snapshot = build_snapshot(profile.required_staff, templates, employees, rules)
    try:
        instance_from_snapshot(snapshot)
    except ValueError as error:
        raise InvalidInputError(str(error)) from error
    return snapshot


async def create_run(session: AsyncSession, payload: SolveRequest) -> SolveRun:
    run = SolveRun(
        demand_profile_id=payload.demand_profile_id,
        status=RunStatus.QUEUED,
        params=solve_params(payload),
        instance_snapshot=await snapshot_for(session, payload),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def execute_run(jobs: JobContext, run_id: int) -> None:
    async with jobs.session_factory() as session:
        run = await session.get(SolveRun, run_id)
        if run is None or run.status is not RunStatus.QUEUED:
            return
        run.status = RunStatus.RUNNING
        await session.commit()
        snapshot = run.instance_snapshot
        params = run.params
    timeout = params["time_limit_seconds"] + JOB_GRACE_SECONDS
    try:
        payload = await run_in_child(jobs, solve_snapshot, snapshot, params, limit_seconds=timeout)
    except TimeoutError:
        await _finish(jobs, run_id, _failure("solver exceeded its time limit"))
        return
    except ModelInvalidError:
        logger.exception("solve run %s: solver rejected the model", run_id)
        await _finish(jobs, run_id, _failure("internal model error"))
        return
    except Exception:
        logger.exception("solve run %s crashed", run_id)
        await _finish(jobs, run_id, _failure("internal error"))
        return
    await _finish(jobs, run_id, _outcome_fields(snapshot, payload))


def _failure(error: str) -> dict[str, Any]:
    return {"status": RunStatus.FAILED, "error": error, "finished_at": _utc_now()}


def _outcome_fields(snapshot: Snapshot, payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "solve_status": payload["solve_status"],
        "objective": payload["objective"],
        "best_bound": payload["bound"],
        "gap": payload["gap"],
        "understaffed_hours": payload["understaffed_hours"],
        "wall_time_seconds": payload["wall_time_seconds"],
        "solver": payload["solver"],
        "solver_version": payload["solver_version"],
        "solver_log": payload["log"],
        "assignments": payload["assignments"],
        "finished_at": _utc_now(),
    }
    if payload["objective"] is None:
        fields.update(
            status=RunStatus.FAILED,
            error=f"no solution found, solver status {payload['solve_status']}",
        )
        return fields
    violations = validate(
        instance_from_snapshot(snapshot), solution_from_rows(payload["assignments"])
    )
    fields["hard_violations"] = len(violations)
    if violations:
        fields.update(
            status=RunStatus.FAILED,
            error=f"validator found {len(violations)} hard-constraint violations",
        )
    else:
        fields.update(status=RunStatus.SUCCEEDED, error=None)
    return fields


async def _finish(jobs: JobContext, run_id: int, fields: dict[str, Any]) -> None:
    async with jobs.session_factory() as session:
        run = await session.get(SolveRun, run_id)
        if run is None:
            return
        for name, value in fields.items():
            setattr(run, name, value)
        await session.commit()


async def get_run(session: AsyncSession, run_id: int) -> SolveRun:
    run = await session.get(SolveRun, run_id)
    if run is None:
        raise NotFoundError(f"solve run {run_id} not found")
    return run


async def list_runs(session: AsyncSession) -> list[SolveRun]:
    result = await session.scalars(
        select(SolveRun).order_by(SolveRun.created_at.desc(), SolveRun.id.desc())
    )
    return list(result)


def _schedule(run: SolveRun) -> tuple[Instance, Solution]:
    if run.assignments is None:
        raise ConflictError(f"solve run {run.id} has no schedule")
    return instance_from_snapshot(run.instance_snapshot), solution_from_rows(run.assignments)


def get_compliance(run: SolveRun) -> ComplianceRead:
    instance, solution = _schedule(run)
    return ComplianceRead(
        run_id=run.id,
        violations=[
            ViolationRead(
                kind=violation.kind.value,
                employee_code=violation.employee_id,
                detail=violation.detail,
                day=violation.day,
                legal_basis=LEGAL_BASIS[violation.kind],
            )
            for violation in validate(instance, solution)
        ],
    )


def get_kpi(run: SolveRun) -> KpiRead:
    instance, solution = _schedule(run)
    measures = kpi.compute_kpi(instance, solution)
    return KpiRead(
        run_id=run.id,
        coverage_ratio=measures.coverage_ratio,
        understaffed_hours=measures.understaffed_hours,
        overstaffed_hours=measures.overstaffed_hours,
        schedule_efficiency=measures.schedule_efficiency,
        labor_cost=measures.labor_cost,
        night_premium_cost=measures.night_premium_cost,
        night_shift_stddev=measures.night_shift_stddev,
        weekend_shift_stddev=measures.weekend_shift_stddev,
        hard_violations=len(validate(instance, solution)),
        staff_by_hour=list(kpi.staff_by_hour(instance, solution)),
        required_by_hour=list(instance.demand),
    )


def assignments_csv(run: SolveRun) -> str:
    instance, _ = _schedule(run)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(ASSIGNMENT_HEADER)
    for row in run.assignments or []:
        shift = instance.shift_by_name(str(row["shift_name"]))
        break_offset = row.get("break_offset")
        writer.writerow(
            [
                row["employee_code"],
                row["day"],
                shift.name,
                shift.start_hour,
                shift.length,
                "" if break_offset is None else break_offset,
            ]
        )
    return buffer.getvalue()


def coverage_csv(run: SolveRun) -> str:
    instance, solution = _schedule(run)
    staffed = kpi.staff_by_hour(instance, solution)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COVERAGE_HEADER)
    for hour, required in enumerate(instance.demand):
        day, hour_of_day = divmod(hour, 24)
        writer.writerow([hour, day, hour_of_day, required, staffed[hour]])
    return buffer.getvalue()


def kpi_csv(read: KpiRead) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(KPI_HEADER)
    for metric, value in read.model_dump(
        exclude={"run_id", "staff_by_hour", "required_by_hour"}
    ).items():
        writer.writerow([metric, value])
    return buffer.getvalue()


async def create_manual_edit(
    session: AsyncSession, base: SolveRun, payload: ManualEditRequest
) -> SolveRun:
    if base.assignments is None:
        raise ConflictError(f"solve run {base.id} has no schedule to edit")
    instance = instance_from_snapshot(base.instance_snapshot)
    employee_codes = {employee.id for employee in instance.employees}
    shift_names = {shift.name for shift in instance.shift_types}
    rows: list[dict[str, Any]] = []
    for item in payload.assignments:
        if item.employee_code not in employee_codes:
            raise InvalidInputError(f"unknown employee {item.employee_code}")
        if item.shift_name not in shift_names:
            raise InvalidInputError(f"unknown shift {item.shift_name}")
        rows.append(item.model_dump())
    solution = solution_from_rows(rows)
    violations = validate(instance, solution)
    run = SolveRun(
        demand_profile_id=base.demand_profile_id,
        parent_run_id=base.id,
        status=RunStatus.FAILED if violations else RunStatus.SUCCEEDED,
        solver="manual",
        params=base.params,
        instance_snapshot=base.instance_snapshot,
        assignments=rows,
        understaffed_hours=kpi.compute_kpi(instance, solution).understaffed_hours,
        hard_violations=len(violations),
        error=f"validator found {len(violations)} hard-constraint violations"
        if violations
        else None,
        finished_at=_utc_now(),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def recover_stale_runs(session: AsyncSession) -> int:
    stale = list(
        await session.scalars(
            select(SolveRun).where(SolveRun.status.in_([RunStatus.QUEUED, RunStatus.RUNNING]))
        )
    )
    for run in stale:
        run.status = RunStatus.FAILED
        run.error = "server restarted"
        run.finished_at = _utc_now()
    await session.commit()
    return len(stale)
