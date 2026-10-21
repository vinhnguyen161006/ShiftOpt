from dataclasses import dataclass

from shiftopt.domain import Instance, Solution
from shiftopt.solvers.base import SolveParams, SolveResult

SOLVER_NAME = "ortools-cp-sat"


@dataclass(frozen=True)
class RosterOutcome:
    solution: Solution
    result: SolveResult
    understaffed_hours: int | None


def solve_roster(instance: Instance, params: SolveParams) -> RosterOutcome:
    """TODO: per-employee roster with Boolean x[e, d, s] solved by CP-SAT on a cyclic week.

    Hard: at most one shift per day, weekly hours (Article 105), rest between shifts from the
    general formula 24 + start' - (start + length) >= 12 (Article 110), maximum consecutive days
    over cyclic windows, a rest day whose surrounding gap is at least 24 hours (Article 111).
    Soft: coverage through shortfall variables u[h] so the model is always feasible.
    Objective: lexicographic. Phase 1 minimizes total shortfall, phase 2 caps it and minimizes
    labor cost with the night premium (Article 98). Symmetry breaking only among employees
    with identical attributes. Status is OPTIMAL only when both phases prove optimality.
    """
    raise NotImplementedError
