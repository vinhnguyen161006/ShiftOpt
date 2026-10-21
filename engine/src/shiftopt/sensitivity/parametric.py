from collections.abc import Sequence

from shiftopt.domain import Instance
from shiftopt.solvers.base import SolveParams, SolveResult


def sweep_demand_multiplier(
    instance: Instance, multipliers: Sequence[float], params: SolveParams
) -> list[tuple[float, SolveResult]]:
    """TODO: re-solve with demand ceil(lambda * r_t) for each lambda (0.8 to 1.3) and return
    z(lambda). A FEASIBLE result must stay flagged so a gap is never read as a cost change."""
    raise NotImplementedError


def discrete_marginal_cost(instance: Instance, params: SolveParams) -> tuple[float, ...]:
    """TODO: for each hour t return z(r + e_t) - z(r) using 168 re-solves; this is the valid
    marginal cost of an integer model, unlike a shadow price."""
    raise NotImplementedError
