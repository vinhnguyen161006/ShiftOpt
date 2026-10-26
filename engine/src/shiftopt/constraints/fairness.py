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
