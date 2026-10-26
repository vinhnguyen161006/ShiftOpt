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


def test_shift_cost_adds_night_premium_article_98() -> None:
    rules = LaborRules()
    assert ShiftType("night", 0).night_hours(rules) == 6
    assert ShiftType("night", 0).cost_per_wage_unit(rules) == 100 * 8 + 30 * 6
    assert ShiftType("day", 8).cost_per_wage_unit(rules) == 100 * 8


def test_night_shift_needs_more_than_half_its_hours_at_night() -> None:
    rules = LaborRules()
    assert ShiftType("late", 22).is_night_shift(rules)
    assert ShiftType("midnight", 0).is_night_shift(rules)
    assert not ShiftType("evening", 16).is_night_shift(rules)
    assert not ShiftType("day", 8).is_night_shift(rules)


def test_instance_shift_by_name_returns_match_or_raises() -> None:
    day = ShiftType("day", 8)
    instance = Instance(demand=(0,) * HOURS_PER_WEEK, employees=(), shift_types=(day,))
    assert instance.shift_by_name("day") == day
    with pytest.raises(KeyError):
        instance.shift_by_name("missing")
