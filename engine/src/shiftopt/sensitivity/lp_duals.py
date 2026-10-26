from collections.abc import Sequence
from dataclasses import dataclass

from shiftopt.domain import Instance
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.sensitivity.parametric import MarginalCostTable
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams, SolveResult, SolveStatus

APPROXIMATE_LABEL = "LP relaxation dual: an approximation, the integrality gap can be large"


@dataclass(frozen=True)
class LpDuals:
    duals: tuple[float, ...]
    missing_hours: tuple[int, ...]
    lp_objective: float
    result: SolveResult
    approximate: bool = True
    label: str = APPROXIMATE_LABEL


@dataclass(frozen=True)
class DualComparison:
    hour: int
    lp_dual: float
    marginal_cost: float | None
    proven: bool


def normalize_duals(raw: Sequence[float | None]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Replace None duals with 0.0 and report which hours had none."""
    missing = tuple(hour for hour, value in enumerate(raw) if value is None)
    return tuple(0.0 if value is None else value for value in raw), missing


def lp_relaxation_duals(
    instance: Instance, hourly_wage: int, params: SolveParams = DEFAULT_PARAMS
) -> LpDuals:
    """Duals of the LP relaxation of the implicit-break model. Duals are only meaningful at an
    LP optimum, so any other status raises."""
    outcome = solve_with_implicit_breaks(instance, hourly_wage, params, relax=True)
    if outcome.result.status != SolveStatus.OPTIMAL or outcome.result.objective is None:
        raise ValueError(f"LP relaxation not optimal: {outcome.result.status}")
    duals, missing = normalize_duals(outcome.duals or ())
    return LpDuals(
        duals=duals,
        missing_hours=missing,
        lp_objective=outcome.result.objective,
        result=outcome.result,
    )


def compare_duals_with_marginal_cost(
    lp: LpDuals, table: MarginalCostTable
) -> tuple[DualComparison, ...]:
    """Place each hour's LP dual beside its integer marginal cost. The gap between the two is
    the integrality effect."""
    return tuple(
        DualComparison(
            hour=entry.hour,
            lp_dual=lp.duals[entry.hour],
            marginal_cost=entry.delta,
            proven=entry.proven,
        )
        for entry in table.hours
    )
