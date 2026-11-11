from dataclasses import asdict
from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules

from src.employees.models import EmployeeRecord
from src.schedules.snapshot import build_snapshot, instance_from_snapshot, solution_from_rows
from src.shifts.models import ShiftTemplate


def _template(name: str, start_hour: int, length_hours: int) -> ShiftTemplate:
    return ShiftTemplate(name=name, start_hour=start_hour, length_hours=length_hours)


def _employee(code: str, unavailable: list[int] | None = None) -> EmployeeRecord:
    return EmployeeRecord(
        code=code,
        name=code,
        hourly_wage=100,
        unavailable_days=unavailable or [],
        preferred_days_off=[],
    )


def _snapshot() -> dict[str, Any]:
    return build_snapshot(
        [1] * 168,
        [_template("night", 22, 8), _template("day", 8, 8)],
        [_employee("E2"), _employee("E1", unavailable=[6, 2])],
        LaborRules(),
    )


def test_snapshot_orders_employees_and_shifts() -> None:
    snapshot = _snapshot()

    assert [row["name"] for row in snapshot["shift_types"]] == ["day", "night"]
    assert [row["id"] for row in snapshot["employees"]] == ["E1", "E2"]
    assert snapshot["employees"][0]["unavailable_days"] == [2, 6]


def test_snapshot_is_deterministic() -> None:
    assert _snapshot() == _snapshot()


def test_instance_round_trips_rules_and_requests() -> None:
    instance = instance_from_snapshot(_snapshot())

    assert instance.rules == LaborRules()
    assert instance.employees[0].unavailable_days == frozenset({2, 6})
    assert instance.shift_by_name("night").start_hour == 22
    assert asdict(instance.rules) == asdict(LaborRules())


def test_employee_weekly_cap_round_trips_and_defaults_for_old_snapshots() -> None:
    snapshot = _snapshot()
    snapshot["employees"][0]["max_weekly_hours"] = 24
    del snapshot["employees"][1]["max_weekly_hours"]

    instance = instance_from_snapshot(snapshot)

    assert instance.employees[0].max_weekly_hours == 24
    assert instance.employees[1].max_weekly_hours is None


def test_rows_and_rules_saved_with_break_fields_still_load() -> None:
    solution = solution_from_rows(
        [{"employee_code": "E1", "day": 0, "shift_name": "day", "break_offset": 3}]
    )
    snapshot = {**_snapshot(), "rules": {**asdict(LaborRules()), "min_break_minutes": 30}}

    assert solution.assignments[0].employee_id == "E1"
    assert instance_from_snapshot(snapshot).rules == LaborRules()


def test_snapshot_round_trips_minimum_hours_and_budget() -> None:
    record = _employee("E1")
    record.min_weekly_hours = 16
    snapshot = build_snapshot(
        [1] * 168, [_template("day", 8, 8)], [record], LaborRules(), weekly_budget=500_000
    )

    instance = instance_from_snapshot(snapshot)

    assert instance.employees[0].min_weekly_hours == 16
    assert instance.weekly_budget == 500_000


def test_old_snapshot_without_budget_still_loads() -> None:
    snapshot = _snapshot()
    del snapshot["weekly_budget"]
    for row in snapshot["employees"]:
        del row["min_weekly_hours"]

    instance = instance_from_snapshot(snapshot)

    assert instance.weekly_budget is None
    assert instance.employees[0].min_weekly_hours is None
