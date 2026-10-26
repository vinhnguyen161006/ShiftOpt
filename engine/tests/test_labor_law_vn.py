from shiftopt.constraints.fairness import night_shift_spread
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.constraints.sequences import (
    consecutive_day_windows,
    forbidden_shift_pairs,
    rest_hours,
)
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.time_grid import HOURS_PER_WEEK
from shiftopt.validation import ViolationKind, validate

DAY = ShiftType("day", 8)
AFTERNOON = ShiftType("afternoon", 14)
MORNING = ShiftType("morning", 6)


def six_day_roster(rules: LaborRules) -> list[ViolationKind]:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(Employee("e1", 100),),
        shift_types=(DAY,),
        rules=rules,
    )
    roster = Solution(tuple(Assignment("e1", day, DAY.name, break_offset=1) for day in range(6)))
    return [violation.kind for violation in validate(instance, roster)]


def test_consecutive_days_rule_permits_six_in_a_row() -> None:
    assert ViolationKind.CONSECUTIVE_DAYS not in six_day_roster(LaborRules())


def test_consecutive_day_windows_wrap_over_the_week() -> None:
    windows = consecutive_day_windows(LaborRules(max_consecutive_days=4))
    assert len(windows) == 7
    assert (5, 6, 0, 1, 2) in windows


def test_consecutive_day_windows_empty_when_longer_than_week() -> None:
    assert consecutive_day_windows(LaborRules(max_consecutive_days=7)) == []


def test_afternoon_then_morning_is_forbidden_pair() -> None:
    assert rest_hours(AFTERNOON, MORNING, 1) == 8
    assert ("afternoon", "morning", 1) in forbidden_shift_pairs((AFTERNOON, MORNING), LaborRules())


def test_general_formula_not_l8_shortcut() -> None:
    short = ShiftType("short", 22, length=4)
    assert rest_hours(short, MORNING, 1) == 24 + 6 - (22 + 4)
    assert rest_hours(short, MORNING, 1) == 4
    long = ShiftType("long", 6, length=10)
    assert rest_hours(long, ShiftType("late", 8), 1) == 24 + 8 - (6 + 10)


def test_forbidden_pairs_match_validator_rest_rule() -> None:
    shifts = (
        AFTERNOON,
        MORNING,
        ShiftType("night", 22),
        ShiftType("midnight", 0),
        ShiftType("evening", 16),
        ShiftType("early", 4, length=6),
    )
    rules = LaborRules()
    forbidden = set(forbidden_shift_pairs(shifts, rules))
    for prev in shifts:
        for nxt in shifts:
            for offset in range(1, 7):
                instance = Instance(
                    demand=(0,) * HOURS_PER_WEEK,
                    employees=(Employee("e1", 100),),
                    shift_types=shifts,
                    rules=rules,
                )
                roster = Solution(
                    (
                        Assignment("e1", 0, prev.name, break_offset=1),
                        Assignment("e1", offset, nxt.name, break_offset=1),
                    )
                )
                flagged = {
                    violation.day
                    for violation in validate(instance, roster)
                    if violation.kind is ViolationKind.REST_BETWEEN_SHIFTS
                }
                assert (offset in flagged) == ((prev.name, nxt.name, offset) in forbidden)


def test_night_spread_is_max_minus_min_over_all_employees() -> None:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(Employee("e1", 100), Employee("e2", 100), Employee("e3", 100)),
        shift_types=(ShiftType("night", 22), DAY),
    )
    solution = Solution(
        (
            Assignment("e1", 0, "night"),
            Assignment("e1", 2, "night"),
            Assignment("e2", 4, "night"),
            Assignment("e2", 5, "day"),
        )
    )
    assert night_shift_spread(instance, solution) == 2


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
