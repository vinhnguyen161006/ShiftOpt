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


def test_solution_rows_keep_break_offset() -> None:
    solution = solution_from_rows(
        [{"employee_code": "E1", "day": 0, "shift_name": "day", "break_offset": 3}]
    )

    assert solution.assignments[0].employee_id == "E1"
    assert solution.assignments[0].break_offset == 3
