from dataclasses import dataclass

import pulp

from shiftopt.domain import Instance, ShiftType
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams, SolveResult
from shiftopt.solvers.pulp_backend import run_problem
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_WEEK, shift_hours

Column = tuple[int, ShiftType]


@dataclass(frozen=True)
class SetCoveringResult:
    """counts maps (day, shift name) to the number of people starting that shift. duals holds the
    LP relaxation duals per hour of the week when relaxed; they approximate marginal cost and are
    never an ILP shadow price."""

    result: SolveResult
    counts: dict[tuple[int, str], float]
    duals: tuple[float | None, ...] | None


def columns_for(instance: Instance) -> tuple[Column, ...]:
    """Every (day, shift) start that fits the daily hour limit (Article 105)."""
    shifts = [
        shift for shift in instance.shift_types if shift.length <= instance.rules.max_daily_hours
    ]
    return tuple((day, shift) for day in range(DAYS_PER_WEEK) for shift in shifts)


def solve_set_covering(
    instance: Instance,
    hourly_wage: int,
    params: SolveParams = DEFAULT_PARAMS,
    relax: bool = False,
) -> SetCoveringResult:
    """Dantzig (1954) set covering over the cyclic week: minimise the cost of shift starts so every
    hour receives its demand. The model is aggregate and carries no per-person rules; it gives
    head counts per shift type, not a roster. relax=True drops integrality and returns duals."""
    problem = pulp.LpProblem("set_covering", pulp.LpMinimize)
    category = pulp.LpContinuous if relax else pulp.LpInteger
    columns = columns_for(instance)
    variables = {
        (day, shift.name): problem.add_variable(f"x_{index}", lowBound=0, cat=category)
        for index, (day, shift) in enumerate(columns)
    }
    rules = instance.rules
    problem += pulp.lpSum(
        hourly_wage * shift.cost_per_wage_unit(rules) * variables[(day, shift.name)]
        for day, shift in columns
    )
    for hour in range(HOURS_PER_WEEK):
        covering = [
            variables[(day, shift.name)]
            for day, shift in columns
            if hour in shift_hours(day, shift.start_hour, shift.length)
        ]
        problem += pulp.lpSum(covering) >= instance.demand[hour], f"cover_{hour}"
    result = run_problem(problem, params, mip=not relax)
    counts = (
        {key: variable.value() or 0.0 for key, variable in variables.items()}
        if result.objective is not None
        else {}
    )
    return SetCoveringResult(result=result, counts=counts, duals=_duals(problem, result, relax))


def _duals(
    problem: pulp.LpProblem, result: SolveResult, relax: bool
) -> tuple[float | None, ...] | None:
    if not relax or result.objective is None:
        return None
    return tuple(
        problem.get_constraint_by_name(f"cover_{hour}").pi for hour in range(HOURS_PER_WEEK)
    )
