from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from shiftopt import kpi
from shiftopt.domain import Instance, Solution
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.models.set_covering_pulp import SetCoveringResult, solve_set_covering
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams, SolveResult, SolveStatus
from shiftopt.staffing.linear import tolerant_ceil

DEFAULT_MULTIPLIERS = (0.8, 0.9, 1.0, 1.1, 1.2, 1.3)


@dataclass(frozen=True)
class Evaluation:
    """Outcome of one re-solve. labor_cost is in hundredths of the wage unit, night premium
    included. staffed_hours counts paid shift hours, breaks included. None means no solution."""

    result: SolveResult
    labor_cost: float | None
    understaffed_hours: int | None
    staffed_hours: int | None

    @property
    def proven(self) -> bool:
        return self.result.status == SolveStatus.OPTIMAL


Resolver = Callable[[Instance], Evaluation]


def aggregate_resolver(
    hourly_wage: int, params: SolveParams = DEFAULT_PARAMS, with_breaks: bool = True
) -> Resolver:
    """Re-solve with the head-count model. Coverage is hard there, so a solution has no
    understaffed hours."""

    def resolve(instance: Instance) -> Evaluation:
        if with_breaks:
            outcome = solve_with_implicit_breaks(instance, hourly_wage, params)
        else:
            outcome = solve_set_covering(instance, hourly_wage, params)
        return _aggregate_evaluation(instance, outcome)

    return resolve


def _aggregate_evaluation(instance: Instance, outcome: SetCoveringResult) -> Evaluation:
    solved = outcome.result.objective is not None
    staffed = (
        sum(
            round(count) * instance.shift_by_name(name).length
            for (_, name), count in outcome.counts.items()
        )
        if solved
        else None
    )
    return Evaluation(
        result=outcome.result,
        labor_cost=outcome.result.objective,
        understaffed_hours=0 if solved else None,
        staffed_hours=staffed,
    )


def roster_resolver(params: SolveParams = DEFAULT_PARAMS) -> Resolver:
    """Re-solve with the per-employee roster. Labor cost comes from kpi, not from the objective,
    because the last lexicographic tier is not a cost."""

    def resolve(instance: Instance) -> Evaluation:
        outcome = solve_roster(instance, params)
        solved = outcome.understaffed_hours is not None
        return Evaluation(
            result=outcome.result,
            labor_cost=float(kpi.labor_cost(instance, outcome.solution)) if solved else None,
            understaffed_hours=outcome.understaffed_hours,
            staffed_hours=_paid_hours(instance, outcome.solution) if solved else None,
        )

    return resolve


def _paid_hours(instance: Instance, solution: Solution) -> int:
    return sum(
        instance.shift_by_name(assignment.shift_name).length for assignment in solution.assignments
    )


def scale_demand(instance: Instance, multiplier: float) -> Instance:
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    return replace(
        instance,
        demand=tuple(tolerant_ceil(multiplier * value) for value in instance.demand),
    )


@dataclass(frozen=True)
class SweepPoint:
    multiplier: float
    evaluation: Evaluation
    proven: bool


def sweep_demand_multiplier(
    instance: Instance,
    multipliers: Sequence[float],
    resolver: Resolver,
) -> list[SweepPoint]:
    points: list[SweepPoint] = []
    for multiplier in multipliers:
        evaluation = resolver(scale_demand(instance, multiplier))
        points.append(SweepPoint(multiplier, evaluation, evaluation.proven))
    return points


@dataclass(frozen=True)
class HourMarginalCost:
    hour: int
    delta: float | None
    proven: bool


@dataclass(frozen=True)
class MarginalCostTable:
    base: Evaluation
    hours: tuple[HourMarginalCost, ...]


def discrete_marginal_cost(instance: Instance, resolver: Resolver) -> MarginalCostTable:
    """delta_t = z(r + e_t) - z(r) by re-solving once per hour. This is the exact marginal cost
    of an integer model, not a shadow price. proven is False when either solve is not OPTIMAL,
    so a gap is never read as a cost change."""
    base = resolver(instance)
    hours: list[HourMarginalCost] = []
    for hour in range(len(instance.demand)):
        demand = list(instance.demand)
        demand[hour] += 1
        bumped = resolver(replace(instance, demand=tuple(demand)))
        delta = None
        if base.labor_cost is not None and bumped.labor_cost is not None:
            delta = bumped.labor_cost - base.labor_cost
        hours.append(HourMarginalCost(hour, delta, base.proven and bumped.proven))
    return MarginalCostTable(base=base, hours=tuple(hours))
