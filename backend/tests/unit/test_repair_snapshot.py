from typing import Any

import pytest
from pydantic import ValidationError
from shiftopt.constraints.labor_law_vn import LaborRules

from src.employees.models import EmployeeRecord
from src.schedules.schemas import AbsenceWrite, RepairRequest
from src.schedules.snapshot import (
    assignment_changes,
    build_snapshot,
    instance_from_snapshot,
    repair_from_snapshot,
    repair_snapshot,
)
from src.schedules.worker import solve_snapshot
from src.shifts.models import ShiftTemplate


def _base() -> dict[str, Any]:
    return build_snapshot(
        [1] * 168,
        [ShiftTemplate(name="day", start_hour=8, length_hours=8)],
        [
            EmployeeRecord(
                code="E1", name="E1", hourly_wage=100, unavailable_days=[], preferred_days_off=[]
            ),
            EmployeeRecord(
                code="E2", name="E2", hourly_wage=100, unavailable_days=[], preferred_days_off=[]
            ),
        ],
        LaborRules(),
    )


def _row(code: str, day: int, shift: str = "day", offset: int | None = 3) -> dict[str, Any]:
    return {"employee_code": code, "day": day, "shift_name": shift, "break_offset": offset}


def test_repair_snapshot_round_trips_baseline_and_pinned() -> None:
    baseline = [_row("E1", 0), _row("E2", 1)]
    pinned = [_row("E1", 4)]

    snapshot = repair_snapshot(
        _base(),
        from_day=2,
        baseline_rows=baseline,
        pinned_rows=pinned,
        absences={},
        demand=None,
    )
    spec = repair_from_snapshot(snapshot)

    assert spec is not None
    assert spec.from_day == 2
    assert [item.employee_id for item in spec.baseline.assignments] == ["E1", "E2"]
    assert spec.pinned[0].employee_id == "E1"
    assert spec.pinned[0].day == 4
    assert spec.pinned[0].break_offset == 3


def test_repair_snapshot_merges_absences_and_replaces_demand() -> None:
    snapshot = repair_snapshot(
        _base(),
        from_day=0,
        baseline_rows=[],
        pinned_rows=[],
        absences={"E1": [5, 2]},
        demand=[2] * 168,
    )

    instance = instance_from_snapshot(snapshot)

    assert instance.employees[0].unavailable_days == frozenset({2, 5})
    assert instance.demand == (2,) * 168


def test_base_snapshot_is_not_mutated() -> None:
    base = _base()
    repair_snapshot(
        base,
        from_day=0,
        baseline_rows=[],
        pinned_rows=[],
        absences={"E1": [3]},
        demand=None,
    )

    assert base["employees"][0]["unavailable_days"] == []
    assert "repair" not in base


def test_plain_snapshot_has_no_repair() -> None:
    assert repair_from_snapshot(_base()) is None


def test_assignment_changes_counts_added_and_removed_shifts() -> None:
    baseline = [_row("E1", 0), _row("E2", 1)]
    rows = [_row("E1", 0), _row("E2", 2)]

    assert assignment_changes(baseline, rows) == 2


def test_moving_a_break_is_not_a_change() -> None:
    assert assignment_changes([_row("E1", 0, offset=1)], [_row("E1", 0, offset=5)]) == 0


def test_absence_rejects_day_outside_week() -> None:
    with pytest.raises(ValidationError):
        AbsenceWrite(employee_code="E1", days=[7])


def test_absence_rejects_empty_day_list() -> None:
    with pytest.raises(ValidationError):
        AbsenceWrite(employee_code="E1", days=[])


def test_repair_request_rejects_bad_from_day() -> None:
    with pytest.raises(ValidationError):
        RepairRequest(from_day=7)


def test_repair_request_defaults_are_empty() -> None:
    payload = RepairRequest(from_day=2)

    assert payload.absences == []
    assert payload.pinned == []
    assert payload.demand_profile_id is None


def test_worker_keeps_fully_locked_baseline() -> None:
    snapshot = build_snapshot(
        [1] * 168,
        [ShiftTemplate(name="day", start_hour=8, length_hours=8)],
        [
            EmployeeRecord(
                code="E1", name="E1", hourly_wage=100, unavailable_days=[], preferred_days_off=[]
            ),
            EmployeeRecord(
                code="E2", name="E2", hourly_wage=100, unavailable_days=[], preferred_days_off=[]
            ),
        ],
        LaborRules(),
    )
    params: dict[str, float] = {
        "time_limit_seconds": 10.0,
        "relative_gap_limit": 0.0,
        "num_workers": 1,
        "random_seed": 0,
    }
    baseline = solve_snapshot(snapshot, params)["assignments"]
    repaired = repair_snapshot(
        snapshot,
        from_day=7,
        baseline_rows=baseline,
        pinned_rows=[],
        absences={},
        demand=None,
    )

    result = solve_snapshot(repaired, params)

    assert sorted(map(str, result["assignments"])) == sorted(map(str, baseline))
