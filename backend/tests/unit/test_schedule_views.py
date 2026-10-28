from dataclasses import asdict
from typing import Any

import pytest
from shiftopt.constraints.labor_law_vn import LaborRules

from src.exceptions import ConflictError
from src.schedules.models import RunStatus, SolveRun
from src.schedules.service import (
    assignments_csv,
    coverage_csv,
    get_compliance,
    get_kpi,
    kpi_csv,
)


def _snapshot() -> dict[str, Any]:
    return {
        "demand": [1 if 8 <= hour < 16 else 0 for hour in range(168)],
        "shift_types": [
            {"name": "evening", "start_hour": 14, "length": 8},
            {"name": "morning", "start_hour": 6, "length": 8},
            {"name": "day", "start_hour": 8, "length": 8},
        ],
        "employees": [
            {"id": "E1", "hourly_wage": 100, "unavailable_days": [], "preferred_days_off": []},
        ],
        "rules": asdict(LaborRules()),
    }


def _run(assignments: list[dict[str, object]]) -> SolveRun:
    return SolveRun(
        id=7,
        status=RunStatus.SUCCEEDED,
        params={"time_limit_seconds": 10.0},
        instance_snapshot=_snapshot(),
        assignments=assignments,
    )


def test_rest_violation_is_reported_with_its_article() -> None:
    run = _run(
        [
            {"employee_code": "E1", "day": 0, "shift_name": "evening", "break_offset": 3},
            {"employee_code": "E1", "day": 1, "shift_name": "morning", "break_offset": 3},
        ]
    )

    violations = get_compliance(run).violations

    rest = [item for item in violations if item.kind == "rest_between_shifts"]
    assert len(rest) == 1
    assert rest[0].legal_basis == "Article 110"


def test_assignments_csv_lists_each_shift() -> None:
    run = _run([{"employee_code": "E1", "day": 0, "shift_name": "day", "break_offset": None}])

    lines = assignments_csv(run).splitlines()

    assert lines[0] == "employee_code,day,shift_name,start_hour,length_hours,break_offset"
    assert lines[1] == "E1,0,day,8,8,"


def test_coverage_csv_has_one_row_per_hour() -> None:
    run = _run([{"employee_code": "E1", "day": 0, "shift_name": "day", "break_offset": None}])

    lines = coverage_csv(run).splitlines()

    assert len(lines) == 169
    assert lines[9] == "8,0,8,1,1"


def test_kpi_csv_carries_coverage_metric() -> None:
    run = _run([{"employee_code": "E1", "day": 0, "shift_name": "day", "break_offset": None}])

    text = kpi_csv(get_kpi(run))

    assert text.splitlines()[0] == "metric,value"
    assert "coverage_ratio," in text


def test_run_without_schedule_has_no_views() -> None:
    run = _run([])
    run.assignments = None

    with pytest.raises(ConflictError):
        get_compliance(run)
