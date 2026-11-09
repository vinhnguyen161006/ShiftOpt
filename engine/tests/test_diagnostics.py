import ast
from pathlib import Path

from shiftopt import diagnostics
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.diagnostics import PreSolveWarning, WarningKind, diagnose
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week

DAY = ShiftType("day", 8)
NIGHT = ShiftType("night", 0)


def instance_of(
    employees: tuple[Employee, ...],
    demand: tuple[int, ...] = (0,) * HOURS_PER_WEEK,
    shifts: tuple[ShiftType, ...] = (DAY, NIGHT),
    rules: LaborRules | None = None,
) -> Instance:
    return Instance(
        demand=demand,
        employees=employees,
        shift_types=shifts,
        rules=rules or LaborRules(),
    )


def day_demand(days: int) -> tuple[int, ...]:
    demand = [0] * HOURS_PER_WEEK
    for day in range(days):
        for hour in range(8, 16):
            demand[hour_of_week(day, hour)] = 1
    return tuple(demand)


def kinds(warnings: tuple[PreSolveWarning, ...]) -> list[WarningKind]:
    return [warning.kind for warning in warnings]


def test_no_warning_when_crew_is_enough() -> None:
    instance = instance_of((Employee("e0", 100),), demand=day_demand(1))

    assert diagnose(instance) == ()


def test_employee_with_every_day_unavailable_is_flagged_by_id() -> None:
    instance = instance_of(
        (Employee("e0", 100, unavailable_days=frozenset(range(7))), Employee("e1", 100)),
        demand=day_demand(1),
    )

    warnings = diagnose(instance)

    assert warnings == (
        PreSolveWarning(WarningKind.NO_AVAILABLE_DAYS, "employee e0 has no available day", "e0"),
    )


def test_total_paid_hours_below_demand_is_flagged() -> None:
    crew = (Employee("e0", 100), Employee("e1", 100))
    instance = instance_of(crew, demand=(1,) * HOURS_PER_WEEK)

    warnings = diagnose(instance)

    assert kinds(warnings) == [WarningKind.CAPACITY_BELOW_DEMAND]
    assert warnings[0].employee_id is None
    assert "96" in warnings[0].detail
    assert "168" in warnings[0].detail


def test_consecutive_day_rule_caps_workable_days_in_capacity() -> None:
    rules = LaborRules(max_consecutive_days=5)
    one = (Employee("e0", 100),)
    fits = instance_of(one, demand=day_demand(5), rules=rules)
    short = instance_of(one, demand=day_demand(6), rules=rules)

    assert diagnose(fits) == ()
    assert kinds(diagnose(short)) == [WarningKind.CAPACITY_BELOW_DEMAND]


def test_unavailable_days_reduce_capacity() -> None:
    crew = (Employee("e0", 100, unavailable_days=frozenset({5, 6})),)
    instance = instance_of(crew, demand=day_demand(5))

    assert diagnose(instance) == ()
    tighter = instance_of(
        (Employee("e0", 100, unavailable_days=frozenset({0, 1, 2})),), demand=day_demand(5)
    )
    assert kinds(diagnose(tighter)) == [WarningKind.CAPACITY_BELOW_DEMAND]


def test_shifts_longer_than_daily_limit_do_not_add_capacity() -> None:
    long_only = (ShiftType("long", 8, length=10),)
    instance = instance_of((Employee("e0", 100),), demand=day_demand(1), shifts=long_only)

    assert kinds(diagnose(instance)) == [WarningKind.CAPACITY_BELOW_DEMAND]


def test_night_demand_without_night_shift_is_flagged() -> None:
    demand = [0] * HOURS_PER_WEEK
    demand[hour_of_week(0, 23)] = 1
    instance = instance_of((Employee("e0", 100),), demand=tuple(demand), shifts=(DAY,))

    assert kinds(diagnose(instance)) == [WarningKind.NO_NIGHT_SHIFT]


def test_night_demand_with_night_shift_is_not_flagged() -> None:
    demand = [0] * HOURS_PER_WEEK
    demand[hour_of_week(0, 23)] = 1
    instance = instance_of((Employee("e0", 100),), demand=tuple(demand), shifts=(NIGHT,))

    assert diagnose(instance) == ()


def test_warnings_follow_employee_order_then_capacity_then_night() -> None:
    demand = [1] * HOURS_PER_WEEK
    instance = instance_of(
        (Employee("e1", 100, unavailable_days=frozenset(range(7))), Employee("e0", 100)),
        demand=tuple(demand),
        shifts=(DAY,),
    )

    assert kinds(diagnose(instance)) == [
        WarningKind.NO_AVAILABLE_DAYS,
        WarningKind.CAPACITY_BELOW_DEMAND,
        WarningKind.NO_NIGHT_SHIFT,
    ]
    assert diagnose(instance) == diagnose(instance)


def test_diagnostics_do_not_depend_on_models_or_solvers() -> None:
    tree = ast.parse(Path(diagnostics.__file__).read_text(encoding="utf-8"))
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert not any(
        name.startswith("shiftopt.models") or name.startswith("shiftopt.solvers")
        for name in modules
        if name
    )
