from typing import Any

from ortools.sat.python import cp_model

from shiftopt.domain import Instance, ShiftType
from shiftopt.models.set_covering_pulp import SetCoveringResult, columns_for
from shiftopt.solvers.base import DEFAULT_PARAMS, SolveParams
from shiftopt.solvers.cpsat import run_cp_model
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week, shift_hours


def solve_with_implicit_breaks_cpsat(
    instance: Instance,
    hourly_wage: int,
    params: SolveParams = DEFAULT_PARAMS,
) -> SetCoveringResult:
    """Same model as solve_with_implicit_breaks (Bechtold-Jacobs style implicit breaks), written
    for CP-SAT so the two solvers can be compared on one instance. Integer variables only, so the
    result carries no duals: CP-SAT is not a source of shadow prices (CLAUDE.md principle 4)."""
    model = cp_model.CpModel()
    columns = columns_for(instance)
    cap = sum(instance.demand)
    starts = {
        (day, shift.name): model.new_int_var(0, cap, f"x_{index}")
        for index, (day, shift) in enumerate(columns)
    }
    slots = _break_slots(model, instance, columns, cap)
    model.minimize(
        sum(
            hourly_wage * shift.cost_per_wage_unit(instance.rules) * starts[(day, shift.name)]
            for day, shift in columns
        )
    )
    for day, shift in columns:
        if shift.break_window(instance.rules):
            model.add(
                sum(
                    variable
                    for slot_day, slot_shift, _, variable in slots
                    if slot_day == day and slot_shift == shift
                )
                == starts[(day, shift.name)]
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
        model.add(sum(present) - sum(on_break) >= instance.demand[hour])
    solver, result = run_cp_model(model, params)
    counts = (
        {key: float(solver.value(variable)) for key, variable in starts.items()}
        if result.objective is not None
        else {}
    )
    return SetCoveringResult(result=result, counts=counts, duals=None)


def _break_slots(
    model: cp_model.CpModel,
    instance: Instance,
    columns: tuple[tuple[int, ShiftType], ...],
    cap: int,
) -> list[tuple[int, ShiftType, int, Any]]:
    slots: list[tuple[int, ShiftType, int, Any]] = []
    for index, (day, shift) in enumerate(columns):
        for offset in shift.break_window(instance.rules):
            variable = model.new_int_var(0, cap, f"y_{index}_{offset}")
            slots.append((day, shift, offset, variable))
    return slots
