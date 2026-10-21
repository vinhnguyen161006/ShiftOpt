from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.models import AnalysisKind, AnalysisRun
from src.analysis.schemas import DemandSweepRequest, LpDualsRequest, MarginalCostRequest


async def create_run(
    session: AsyncSession,
    kind: AnalysisKind,
    request: DemandSweepRequest | MarginalCostRequest | LpDualsRequest,
) -> AnalysisRun:
    """TODO: validate limits, insert the analysis run as queued and return it."""
    raise NotImplementedError


async def execute_run(run_id: int) -> None:
    """TODO: dispatch on kind in a child process. demand_sweep calls
    shiftopt.sensitivity.parametric.sweep_demand_multiplier, marginal_cost calls
    discrete_marginal_cost, lp_duals calls lp_duals.lp_relaxation_duals. Store the result and
    mark the run succeeded or failed. LP duals must be labeled approximate."""
    raise NotImplementedError


async def get_run(session: AsyncSession, run_id: int) -> AnalysisRun:
    """TODO: return one analysis run or raise NotFoundError."""
    raise NotImplementedError
