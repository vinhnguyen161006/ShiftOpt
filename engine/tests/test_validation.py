import pytest


@pytest.mark.skip(reason="TODO")
def test_clean_roster_has_no_violations() -> None:
    """TODO: five day shifts in a row give no violation."""


@pytest.mark.skip(reason="TODO")
def test_afternoon_then_morning_breaks_rest_rule() -> None:
    """TODO: 14h-22h then 06h-14h is reported with an 8h rest (Article 110)."""


@pytest.mark.skip(reason="TODO")
def test_rest_rule_wraps_from_sunday_to_monday() -> None:
    """TODO: evening on Sunday then night on Monday is reported."""


@pytest.mark.skip(reason="TODO")
def test_seven_working_days_breaks_consecutive_days() -> None:
    """TODO: working all 7 days is reported."""


@pytest.mark.skip(reason="TODO")
def test_consecutive_run_wraps_over_week_boundary() -> None:
    """TODO: a run across Sunday and Monday counts as one run."""


@pytest.mark.skip(reason="TODO")
def test_more_than_48_hours_breaks_weekly_hours() -> None:
    """TODO: 7 shifts of 8h are reported (Article 105)."""


@pytest.mark.skip(reason="TODO")
def test_staircase_roster_never_rests_24_hours() -> None:
    """TODO: a roster whose longest gap is 21h is reported (Article 111)."""


@pytest.mark.skip(reason="TODO")
def test_two_shifts_on_one_day_are_reported() -> None:
    """TODO: duplicate (employee, day) is reported."""


@pytest.mark.skip(reason="TODO")
def test_unknown_employee_and_shift_are_reported() -> None:
    """TODO: unknown ids and shift names are reported."""
