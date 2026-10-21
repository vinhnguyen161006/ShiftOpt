import pytest


@pytest.mark.skip(reason="TODO")
def test_required_staff_applies_ceil_and_floors() -> None:
    """TODO: ceil(alpha * load / productivity) with day and night floors."""


@pytest.mark.skip(reason="TODO")
def test_required_staff_rejects_bad_input() -> None:
    """TODO: wrong length and non-positive alpha raise ValueError."""


@pytest.mark.skip(reason="TODO")
def test_kpi_for_single_day_shift() -> None:
    """TODO: coverage 8/168, understaffed 160, efficiency 21, cost 100 * 800."""


@pytest.mark.skip(reason="TODO")
def test_night_premium_is_added_to_cost() -> None:
    """TODO: a 00h shift costs 100 * (800 + 30 * 6)."""
