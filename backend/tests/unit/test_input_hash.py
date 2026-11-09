from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules

from src.employees.models import EmployeeRecord
from src.schedules.snapshot import REPAIR_KEY, build_snapshot, input_hash
from src.shifts.models import ShiftTemplate


def _snapshot(wage: int = 100) -> dict[str, Any]:
    employee = EmployeeRecord(
        code="E1",
        name="E1",
        hourly_wage=wage,
        unavailable_days=[],
        preferred_days_off=[],
    )
    template = ShiftTemplate(name="day", start_hour=8, length_hours=8)
    return build_snapshot([1] * 168, [template], [employee], LaborRules())


def test_hash_is_stable_for_the_same_inputs() -> None:
    assert input_hash(_snapshot()) == input_hash(_snapshot())
    assert len(input_hash(_snapshot())) == 64


def test_hash_ignores_key_order() -> None:
    snapshot = _snapshot()
    reordered = dict(reversed(list(snapshot.items())))

    assert input_hash(reordered) == input_hash(snapshot)


def test_hash_changes_when_an_input_changes() -> None:
    assert input_hash(_snapshot(100)) != input_hash(_snapshot(101))


def test_hash_ignores_the_repair_part() -> None:
    snapshot = _snapshot()
    repaired = {**snapshot, REPAIR_KEY: {"from_day": 3, "baseline": [], "pinned": []}}

    assert input_hash(repaired) == input_hash(snapshot)
