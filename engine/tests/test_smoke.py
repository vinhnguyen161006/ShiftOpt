import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType
from shiftopt.time_grid import HOURS_PER_WEEK


def test_labor_rules_defaults_follow_the_labor_code() -> None:
    rules = LaborRules()
    assert rules.max_weekly_hours == 48
    assert rules.min_rest_between_shifts == 12
    assert rules.weekly_rest_hours == 24
    assert (rules.night_start, rules.night_end) == (22, 6)


def test_instance_rejects_wrong_demand_length() -> None:
    with pytest.raises(ValueError, match="168"):
        Instance(demand=(1,), employees=(), shift_types=())


def test_instance_rejects_duplicate_employee_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        Instance(
            demand=(0,) * HOURS_PER_WEEK,
            employees=(Employee("a", 1), Employee("a", 1)),
            shift_types=(ShiftType("day", 8),),
        )


def test_assignment_rejects_day_outside_week() -> None:
    with pytest.raises(ValueError, match="day"):
        Assignment("a", 7, "day")
