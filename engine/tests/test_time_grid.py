import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import (
    covers_hour,
    hour_of_week,
    is_night_hour,
    night_hours_in_shift,
    shift_hours,
)

RULES = LaborRules()


def test_hour_of_week_counts_from_monday_midnight() -> None:
    assert hour_of_week(0, 0) == 0
    assert hour_of_week(1, 0) == 24
    assert hour_of_week(6, 23) == 167


def test_overnight_shift_wraps_into_next_day() -> None:
    assert shift_hours(0, 22, 8) == tuple(range(22, 30))


def test_last_day_overnight_shift_wraps_into_monday() -> None:
    assert shift_hours(6, 22, 8) == (166, 167, 0, 1, 2, 3, 4, 5)


def test_night_window_wraps_past_midnight() -> None:
    for hour in (22, 23, 0, 1, 2, 3, 4, 5):
        assert is_night_hour(hour, RULES.night_start, RULES.night_end)
    for hour in (6, 12, 21):
        assert not is_night_hour(hour, RULES.night_start, RULES.night_end)


def test_night_window_accepts_hour_of_week() -> None:
    assert is_night_hour(166, RULES.night_start, RULES.night_end)
    assert not is_night_hour(160, RULES.night_start, RULES.night_end)


@pytest.mark.parametrize(
    ("start_hour", "expected"),
    [(0, 6), (8, 0), (16, 2), (22, 8)],
)
def test_night_hours_in_shift(start_hour: int, expected: int) -> None:
    assert night_hours_in_shift(start_hour, 8, RULES.night_start, RULES.night_end) == expected


def test_night_hours_follow_shift_length() -> None:
    assert night_hours_in_shift(18, 12, RULES.night_start, RULES.night_end) == 8


@pytest.mark.parametrize(
    ("hour", "start_hour", "period", "expected"),
    [
        (5, 22, 24, True),
        (6, 22, 24, False),
        (2, 166, 168, True),
        (6, 166, 168, False),
    ],
)
def test_covers_hour_wraps_on_cyclic_period(
    hour: int, start_hour: int, period: int, expected: bool
) -> None:
    assert covers_hour(hour, start_hour, 8, period) is expected
