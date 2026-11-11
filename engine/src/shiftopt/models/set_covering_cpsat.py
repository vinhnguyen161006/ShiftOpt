from ortools.sat.python import cp_model

from shiftopt.domain import Instance
from shiftopt.models.set_covering_pulp import SetCoveringResult, columns_for
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams
from shiftopt.solvers.cpsat import run_cp_model
from shiftopt.time_grid import HOURS_PER_WEEK, shift_hours


def solve_set_covering_cpsat(
    instance: Instance,
    hourly_wage: int,
    params: SolveParams = DEFAULT_PARAMS,
) -> SetCoveringResult:
    """Same model as solve_set_covering (Dantzig set covering on the cyclic week), written for
    CP-SAT so the two solvers can be compared on one instance. Integer variables only, so the
    result carries no duals: CP-SAT is not a source of shadow prices (CLAUDE.md principle 4)."""
    model = cp_model.CpModel()
    columns = columns_for(instance)
    cap = sum(instance.demand)
    starts = {
        (day, shift.name): model.new_int_var(0, cap, f"x_{index}")
        for index, (day, shift) in enumerate(columns)
    }
    model.minimize(
        sum(
            hourly_wage * shift.cost_per_wage_unit(instance.rules) * starts[(day, shift.name)]
            for day, shift in columns
        )
    )
    for hour in range(HOURS_PER_WEEK):
        model.add(
            sum(
                starts[(day, shift.name)]
                for day, shift in columns
                if hour in shift_hours(day, shift.start_hour, shift.length)
            )
            >= instance.demand[hour]
        )
    solver, result = run_cp_model(model, params)
    counts = (
        {key: float(solver.value(variable)) for key, variable in starts.items()}
        if result.objective is not None
        else {}
    )
    return SetCoveringResult(result=result, counts=counts, duals=None)
