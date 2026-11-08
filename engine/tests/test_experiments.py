import pytest

from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.experiments import (
    SIX_START_HOURS,
    demand_scenarios,
    shift_pattern_scenarios,
    staffing_scenarios,
)
from shiftopt.sensitivity.parametric import DEFAULT_MULTIPLIERS

SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def base(employees: int = 6) -> Instance:
    demand = tuple(3 if 8 <= hour % 24 < 16 else 0 for hour in range(168))
    staff = tuple(Employee(f"e{i:02d}", 100) for i in range(employees))
    return Instance(demand, staff, SHIFTS)


def test_demand_scenarios_include_base_and_every_multiplier() -> None:
    scenarios = demand_scenarios(base())
    assert [s.name for s in scenarios] == ["base"] + [
        f"lambda={m:.1f}" for m in DEFAULT_MULTIPLIERS
    ]


def test_scaled_demand_uses_tolerant_ceiling() -> None:
    scenario = {s.name: s for s in demand_scenarios(base(), multipliers=(1.1,))}["lambda=1.1"]
    assert scenario.instance.demand[8] == 4
    assert scenario.instance.demand[0] == 0


def test_base_instance_is_not_changed_by_scenarios() -> None:
    original = base()
    demand_scenarios(original)
    assert original.demand[8] == 3


def test_staffing_scenarios_remove_the_last_employees_by_id() -> None:
    scenarios = {s.name: s for s in staffing_scenarios(base(8))}
    assert [e.id for e in scenarios["minus-1"].instance.employees] == [
        f"e{i:02d}" for i in range(7)
    ]
    assert len(scenarios["minus-5"].instance.employees) == 3


def test_staffing_scenarios_reject_removing_everyone() -> None:
    with pytest.raises(ValueError, match="cannot remove 2 of 2"):
        staffing_scenarios(base(2), removals=(2,))


def test_six_start_pattern_has_six_distinct_eight_hour_shifts() -> None:
    scenarios = {s.name: s for s in shift_pattern_scenarios(base())}
    six = scenarios["shifts-6"].instance.shift_types
    assert [shift.start_hour for shift in six] == list(SIX_START_HOURS)
    assert {shift.length for shift in six} == {8}
    assert len({shift.name for shift in six}) == 6
    assert scenarios["shifts-3"].instance.shift_types == SHIFTS
