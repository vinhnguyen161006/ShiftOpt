from shiftopt.domain import Instance
from shiftopt.models.set_covering_pulp import SetCoveringResult
from shiftopt.solvers.base import SolveParams


def solve(
    instance: Instance, hourly_wage: int, params: SolveParams, relax: bool = False
) -> SetCoveringResult:
    """TODO: thin adapter that calls models/set_covering_pulp.solve_set_covering with HiGHS.

    Targets the pinned PuLP 3.3.2 with pulp.HiGHS; PuLP 4 changes prob.solve() and
    prob.constraints(), so re-check this adapter before upgrading. When relax=True the LP
    relaxation is solved and constraint duals are forwarded to the result; they are
    approximations, not valid ILP shadow prices (Section 6, invariant 4).
    """
    raise NotImplementedError
