from sqlalchemy.ext.asyncio import AsyncSession

from src.schedules.models import SolveRun
from src.schedules.schemas import ComplianceRead, KpiRead, SolveRequest


async def create_run(session: AsyncSession, payload: SolveRequest) -> SolveRun:
    """TODO: build the shiftopt Instance from the demand profile, shift templates and employees,
    enforce Settings.max_employees and max_solve_seconds (InstanceTooLargeError), store the
    instance snapshot and params, insert the run as queued and return it."""
    raise NotImplementedError


async def execute_run(run_id: int) -> None:
    """TODO: run shiftopt.models.roster_cpsat.solve_roster in a child process
    (ProcessPoolExecutor), never on the event loop. Mark the run running, store status,
    objective, bound, gap, understaffed hours, wall time and log, then mark it succeeded or
    failed with a readable error. Validate the solution with shiftopt.validation before saving."""
    raise NotImplementedError


async def get_run(session: AsyncSession, run_id: int) -> SolveRun:
    """TODO: return one run or raise NotFoundError."""
    raise NotImplementedError


async def list_runs(session: AsyncSession) -> list[SolveRun]:
    """TODO: return runs newest first."""
    raise NotImplementedError


async def get_compliance(session: AsyncSession, run_id: int) -> ComplianceRead:
    """TODO: run shiftopt.validation.validate on the stored solution against the snapshot."""
    raise NotImplementedError


async def get_kpi(session: AsyncSession, run_id: int) -> KpiRead:
    """TODO: compute shiftopt.kpi for the stored solution against the snapshot."""
    raise NotImplementedError


async def recover_stale_runs(session: AsyncSession) -> int:
    """TODO: mark runs left in status running as failed with the reason 'server restarted' and
    return how many were changed. Call it from the application lifespan."""
    raise NotImplementedError
