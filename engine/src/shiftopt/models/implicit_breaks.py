import pulp

from shiftopt.domain import Instance, ShiftType
from shiftopt.models.set_covering_pulp import SetCoveringResult, columns_for
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams
from shiftopt.solvers.pulp_backend import run_problem
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week, shift_hours


def solve_with_implicit_breaks(
    instance: Instance, hourly_wage: int, params: SolveParams = DEFAULT_PARAMS
) -> SetCoveringResult:
    """Bechtold-Jacobs style implicit break model. Each worker of a shift that needs a break is
    counted once in x and once in one break slot y[d, s, k] inside the break window; the break
    removes that worker from coverage in hour k. This has the same optimum as enumerating every
    (shift, break position) column, with one variable per break slot instead. Breaks are whole
    hours, so a 30 or 45 minute break takes a full hour: a conservative approximation."""
    problem = pulp.LpProblem("set_covering_breaks", pulp.LpMinimize)
    rules = instance.rules
    columns = columns_for(instance)
    starts = {
        (day, shift.name): problem.add_variable(f"x_{index}", lowBound=0, cat=pulp.LpInteger)
        for index, (day, shift) in enumerate(columns)
    }
    slots: list[tuple[int, ShiftType, int, pulp.LpVariable]] = []
    for index, (day, shift) in enumerate(columns):
        for offset in shift.break_window(rules):
            variable = problem.add_variable(f"y_{index}_{offset}", lowBound=0, cat=pulp.LpInteger)
            slots.append((day, shift, offset, variable))
    problem += pulp.lpSum(
        hourly_wage * shift.cost_per_wage_unit(rules) * starts[(day, shift.name)]
        for day, shift in columns
    )
    for day, shift in columns:
        window = shift.break_window(rules)
        if window:
            problem += (
                pulp.lpSum(
                    variable
                    for slot_day, slot_shift, _, variable in slots
                    if slot_day == day and slot_shift == shift
                )
                == starts[(day, shift.name)],
                f"break_{day}_{shift.name}",
            )
    for hour in range(HOURS_PER_WEEK):
        present = [
            starts[(day, shift.name)]
            for day, shift in columns
            if hour in shift_hours(day, shift.start_hour, shift.length)
        ]
        on_break = [
            variable
            for day, shift, offset, variable in slots
            if hour_of_week(day, shift.start_hour + offset) == hour
        ]
        problem += (
            pulp.lpSum(present) - pulp.lpSum(on_break) >= instance.demand[hour],
            f"cover_{hour}",
        )
    result = run_problem(problem, params, mip=True)
    counts = (
        {key: variable.value() or 0.0 for key, variable in starts.items()}
        if result.objective is not None
        else {}
    )
    return SetCoveringResult(result=result, counts=counts, duals=None)
