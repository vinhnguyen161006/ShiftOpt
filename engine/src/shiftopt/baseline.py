import time

from shiftopt import kpi
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.sensitivity.parametric import Evaluation, Resolver
from shiftopt.solvers.base import SolveResult, SolveStatus
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_WEEK, hour_of_week, shift_hours
from shiftopt.validation import validate

GREEDY_SOLVER = "greedy"
GREEDY_VERSION = "builtin-1"
_EMPTY_DEMAND = (0,) * HOURS_PER_WEEK


def greedy_roster(instance: Instance) -> Solution:
    """Heuristic baseline for comparison, not an optimiser. Repeatedly takes the (day, shift)
    that covers the most still-short hours, places a rest break in the hour with the most spare
    staff, and gives the shift to the least-loaded employee whose own schedule still passes
    validate. Every hard constraint is per employee, so this per-employee check keeps the whole
    roster legal; the caller still validates the full roster."""
    shifts = tuple(s for s in instance.shift_types if s.length <= instance.rules.max_daily_hours)
    staff = [0] * HOURS_PER_WEEK
    chosen: dict[str, list[Assignment]] = {employee.id: [] for employee in instance.employees}
    hours = dict.fromkeys(chosen, 0)
    spent = 0
    while True:
        options = _ranked_options(instance, shifts, staff)
        if not options:
            break
        placed = False
        for _, day, shift, offset in options:
            employee = _pick_employee(instance, chosen, hours, spent, day, shift, offset)
            if employee is None:
                continue
            _place(instance, staff, chosen, hours, employee, day, shift, offset)
            spent += _shift_cost(instance, employee, shift)
            placed = True
            break
        if not placed:
            break
    return Solution(
        tuple(
            sorted(
                (a for rows in chosen.values() for a in rows),
                key=lambda a: (a.day, a.employee_id, a.shift_name),
            )
        )
    )


def _ranked_options(
    instance: Instance, shifts: tuple[ShiftType, ...], staff: list[int]
) -> list[tuple[int, int, ShiftType, int | None]]:
    options = []
    for day in range(DAYS_PER_WEEK):
        for shift in shifts:
            offset = _break_offset(instance, staff, day, shift)
            gain = _gain(instance, staff, day, shift, offset)
            if gain > 0:
                options.append((-gain, day, shift, offset))
    options.sort(key=lambda option: (option[0], option[1], option[2].start_hour, option[2].name))
    return options


def _break_offset(instance: Instance, staff: list[int], day: int, shift: ShiftType) -> int | None:
    window = shift.break_window(instance.rules)
    if not window:
        return None
    return min(
        window,
        key=lambda offset: (
            _spare(instance, staff, hour_of_week(day, shift.start_hour + offset)),
            offset,
        ),
    )


def _spare(instance: Instance, staff: list[int], hour: int) -> int:
    return instance.demand[hour] - staff[hour]


def _gain(
    instance: Instance, staff: list[int], day: int, shift: ShiftType, offset: int | None
) -> int:
    break_hour = None if offset is None else hour_of_week(day, shift.start_hour + offset)
    return sum(
        1
        for hour in shift_hours(day, shift.start_hour, shift.length)
        if hour != break_hour and _spare(instance, staff, hour) > 0
    )


def _pick_employee(
    instance: Instance,
    chosen: dict[str, list[Assignment]],
    hours: dict[str, int],
    spent: int,
    day: int,
    shift: ShiftType,
    offset: int | None,
) -> Employee | None:
    ranked = sorted(instance.employees, key=lambda e: (hours[e.id], e.hourly_wage, e.id))
    budget = instance.weekly_budget
    for employee in ranked:
        if budget is not None and spent + _shift_cost(instance, employee, shift) > budget:
            continue
        candidate = Assignment(employee.id, day, shift.name, offset)
        single = Instance(_EMPTY_DEMAND, (employee,), instance.shift_types, instance.rules)
        if not validate(single, Solution((*chosen[employee.id], candidate))):
            return employee
    return None


def _shift_cost(instance: Instance, employee: Employee, shift: ShiftType) -> int:
    return employee.hourly_wage * shift.cost_per_wage_unit(instance.rules)


def _place(
    instance: Instance,
    staff: list[int],
    chosen: dict[str, list[Assignment]],
    hours: dict[str, int],
    employee: Employee,
    day: int,
    shift: ShiftType,
    offset: int | None,
) -> None:
    chosen[employee.id].append(Assignment(employee.id, day, shift.name, offset))
    hours[employee.id] += shift.length
    for hour in shift_hours(day, shift.start_hour, shift.length):
        staff[hour] += 1
    if offset is not None:
        staff[hour_of_week(day, shift.start_hour + offset)] -= 1


def greedy_resolver() -> Resolver:
    """Same shape as roster_resolver so the experiment runner can compare the two. Never reports
    OPTIMAL: greedy proves nothing about the optimum."""

    def resolve(instance: Instance) -> Evaluation:
        started = time.perf_counter()
        solution = greedy_roster(instance)
        wall = time.perf_counter() - started
        cost = float(kpi.labor_cost(instance, solution))
        result = SolveResult(
            status=SolveStatus.FEASIBLE,
            objective=cost,
            bound=None,
            gap=None,
            wall_time_seconds=wall,
            solver=GREEDY_SOLVER,
            solver_version=GREEDY_VERSION,
        )
        return Evaluation(
            result=result,
            labor_cost=cost,
            understaffed_hours=kpi.compute_kpi(instance, solution).understaffed_hours,
            staffed_hours=sum(
                instance.shift_by_name(a.shift_name).length for a in solution.assignments
            ),
            staff_by_hour=kpi.staff_by_hour(instance, solution),
        )

    return resolve
