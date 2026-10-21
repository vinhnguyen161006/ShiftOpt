import pytest


@pytest.mark.skip(reason="TODO")
def test_overnight_shift_wraps_into_next_day() -> None:
    """TODO: shift_hours(0, 22, 8) ends at hour 5 of the next day."""


@pytest.mark.skip(reason="TODO")
def test_last_day_overnight_shift_wraps_into_monday() -> None:
    """TODO: shift_hours(6, 22, 8) stays below 168 and ends at hour 5."""


@pytest.mark.skip(reason="TODO")
def test_night_window_wraps_past_midnight() -> None:
    """TODO: 22, 23, 0..5 are night hours; 6 and 21 are not."""


@pytest.mark.skip(reason="TODO")
def test_night_hours_in_shift() -> None:
    """TODO: shifts at 0, 8, 16 and 22 have 6, 0, 2 and 8 night hours."""
