from shiftopt.domain import Instance, Solution


def night_shift_spread(instance: Instance, solution: Solution) -> int:
    """max - min of night shifts per employee over every employee in the instance, so an idle
    employee counts as zero. The roster model minimises this same quantity through
    AddMaxEquality and AddMinEquality. The KPI reports the standard deviation instead, which is a
    descriptive measure and not a linear model term. Unknown shift names raise KeyError."""
    counts = {employee.id: 0 for employee in instance.employees}
    for assignment in solution.assignments:
        shift = instance.shift_by_name(assignment.shift_name)
        if assignment.employee_id in counts and shift.is_night_shift(instance.rules):
            counts[assignment.employee_id] += 1
    if not counts:
        return 0
    return max(counts.values()) - min(counts.values())


def min_hours_shortfall(instance: Instance, solution: Solution) -> int:
    """Total hours by which employees fall short of their contract minimum, counting each shift
    at its full length. Employees without a minimum count as zero. Unknown shift names raise
    KeyError."""
    hours = _hours_by_employee(instance, solution)
    return sum(
        max(0, employee.min_weekly_hours - hours[employee.id])
        for employee in instance.employees
        if employee.min_weekly_hours is not None
    )


def worked_hours_spread(instance: Instance, solution: Solution) -> int:
    """max - min of worked hours per employee, counting each shift at its full length (breaks are
    not subtracted, as in the weekly-hours rule). Idle employees count as zero. The roster model
    minimises the same quantity through AddMaxEquality and AddMinEquality when
    cost_tolerance_percent is positive. Unknown shift names raise KeyError."""
    hours = _hours_by_employee(instance, solution)
    if not hours:
        return 0
    return max(hours.values()) - min(hours.values())


def _hours_by_employee(instance: Instance, solution: Solution) -> dict[str, int]:
    hours = {employee.id: 0 for employee in instance.employees}
    for assignment in solution.assignments:
        if assignment.employee_id in hours:
            hours[assignment.employee_id] += instance.shift_by_name(assignment.shift_name).length
    return hours
