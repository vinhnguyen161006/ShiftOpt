from dataclasses import dataclass

from shiftopt.domain import Instance
from shiftopt.solvers.base import SolveStatus

SOLVER_NAME = "pulp-highs"


@dataclass(frozen=True)
class SetCoveringResult:
    """counts maps (day, shift name) to head count. duals holds the LP relaxation duals per hour
    of the week when relaxed; they approximate marginal cost and are never an ILP shadow price.
    """

    status: SolveStatus
    objective: float | None
    counts: dict[tuple[int, str], float]
    duals: tuple[float | None, ...] | None


def solve_set_covering(
    instance: Instance, hourly_wage: int, relax: bool = False
) -> SetCoveringResult:
    """TODO: Dantzig (1954) set covering over a cyclic week with PuLP and HiGHS.

    Integer x[d, s] is how many people start shift type s on day d; every hour must reach its
    demand at minimum cost. relax=True drops integrality and returns constraint duals.
    """
    raise NotImplementedError
