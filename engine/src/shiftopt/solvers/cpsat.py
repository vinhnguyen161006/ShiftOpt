from shiftopt.domain import Instance, Solution
from shiftopt.solvers.base import SolveParams, SolveResult


def solve(instance: Instance, params: SolveParams) -> tuple[Solution | None, SolveResult]:
    """TODO: run CP-SAT on the roster model from models/roster_cpsat.py.

    Translates the Instance into CP-SAT variables x[e, d, s] Boolean, adds hard constraints from
    LaborRules (Section 5.3) and runs a lexicographic two-phase objective: minimise total shortfall
    u_h first (phase 1), then fix the shortfall ceiling and minimise labour cost (phase 2).

    Solver is invoked in the calling process; the caller (schedules/service.py) is responsible for
    running this inside a ProcessPoolExecutor so the FastAPI event loop is never blocked (Section
    3.3). Returns (None, result) when the model is INFEASIBLE or UNKNOWN.
    """
    raise NotImplementedError
