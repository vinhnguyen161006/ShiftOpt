import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.time_grid import HOURS_PER_WEEK
from shiftopt.validation import ViolationKind, validate

DAY = ShiftType("day", 8)


def six_day_roster(rules: LaborRules) -> list[ViolationKind]:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(Employee("e1", 100),),
        shift_types=(DAY,),
        rules=rules,
    )
    roster = Solution(tuple(Assignment("e1", day, DAY.name) for day in range(6)))
    return [violation.kind for violation in validate(instance, roster)]


def test_consecutive_days_rule_permits_six_in_a_row() -> None:
    assert ViolationKind.CONSECUTIVE_DAYS not in six_day_roster(LaborRules())


@pytest.mark.skip(reason="TODO")
def test_consecutive_day_windows_wrap_over_the_week() -> None:
    """TODO: with max_consecutive_days = 4, the window starting on Saturday is (5, 6, 0, 1, 2)."""


@pytest.mark.skip(reason="TODO")
def test_afternoon_then_morning_is_forbidden_pair() -> None:
    """TODO: (14h-22h, 06h-14h) is in the output of forbidden_shift_pairs; this is the required
    test from Section 5.3. Rest = 24 + 6 - (14 + 8) = 8 < 12."""


@pytest.mark.skip(reason="TODO")
def test_general_formula_not_l8_shortcut() -> None:
    """TODO: a shift of length != 8 must still use the general formula 24 + sigma' - (sigma + L)
    and not the shortcut sigma - sigma' > 4."""


def test_weekly_hours_limit_48() -> None:
    assert LaborRules().max_weekly_hours == 48
    assert ViolationKind.WEEKLY_HOURS not in six_day_roster(LaborRules())
    assert ViolationKind.WEEKLY_HOURS in six_day_roster(LaborRules(max_weekly_hours=40))


def test_night_premium_percent_30() -> None:
    assert LaborRules().night_premium_percent == 30
    night = ShiftType("night", 0)
    assert night.cost_per_wage_unit(LaborRules(night_premium_percent=50)) == 100 * 8 + 50 * 6


def test_break_minimums_follow_article_109() -> None:
    rules = LaborRules()
    assert (rules.min_break_minutes, rules.min_night_break_minutes) == (30, 45)
