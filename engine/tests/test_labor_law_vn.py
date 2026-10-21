import pytest


@pytest.mark.skip(reason="TODO")
def test_consecutive_days_rule_permits_six_in_a_row() -> None:
    """TODO: six consecutive working days must not be flagged (max_consecutive_days = 6)."""


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


@pytest.mark.skip(reason="TODO")
def test_weekly_hours_limit_48() -> None:
    """TODO: LaborRules default max_weekly_hours is 48 (Article 105)."""


@pytest.mark.skip(reason="TODO")
def test_night_premium_percent_30() -> None:
    """TODO: LaborRules default night_premium_percent is 30 (Article 98 clause 2)."""
