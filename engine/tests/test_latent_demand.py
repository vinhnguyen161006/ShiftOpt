from datetime import date, timedelta

import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.staffing.latent_demand import ProductDay, weekly_load, zero_night_load
from shiftopt.staffing.linear import required_staff
from shiftopt.time_grid import HOURS_PER_DAY, HOURS_PER_WEEK

RULES = LaborRules()
START = date(2024, 6, 3)
MONDAY_TEN = 10


def _product_week(
    product_id: int,
    sale: float,
    weeks: int = 1,
    stockout: frozenset[tuple[int, int]] = frozenset(),
    stockout_sale: float = 0.0,
) -> list[ProductDay]:
    rows: list[ProductDay] = []
    for index in range(7 * weeks):
        flags = tuple(1 if (index, hour) in stockout else 0 for hour in range(HOURS_PER_DAY))
        sales = tuple(stockout_sale if flags[hour] else sale for hour in range(HOURS_PER_DAY))
        rows.append(ProductDay(product_id, START + timedelta(days=index), sales, flags))
    return rows


def test_products_are_summed_per_hour() -> None:
    rows = _product_week(1, 1.0) + _product_week(2, 2.0)
    result = weekly_load(rows)
    assert len(result.load) == HOURS_PER_WEEK
    assert result.load[MONDAY_TEN] == 3.0


def test_stockout_hour_takes_mean_of_same_product_weekday_hour() -> None:
    rows = _product_week(
        1, 4.0, weeks=2, stockout=frozenset({(0, MONDAY_TEN)}), stockout_sale=100.0
    )
    result = weekly_load(rows)
    assert result.load[MONDAY_TEN] == 4.0
    assert result.imputed_cells == 1
    assert result.unimputed_cells == 0


def test_fully_stocked_out_cell_keeps_observed_sale() -> None:
    rows = _product_week(1, 4.0, stockout=frozenset({(0, MONDAY_TEN)}), stockout_sale=100.0)
    result = weekly_load(rows)
    assert result.load[MONDAY_TEN] == 100.0
    assert result.imputed_cells == 0
    assert result.unimputed_cells == 1


def test_weekly_load_keeps_night_hours() -> None:
    result = weekly_load(_product_week(1, 4.0))
    assert result.load[0] == 4.0


def test_night_hours_are_zeroed_and_floor_comes_from_night_min_staff() -> None:
    load, floored = zero_night_load(weekly_load(_product_week(1, 4.0)).load, RULES)
    assert load[0] == 0.0
    assert load[23] == 0.0
    assert load[MONDAY_TEN] == 4.0
    assert floored == 7 * 8
    staff = required_staff(
        load,
        alpha=1.0,
        productivity=1.0,
        min_staff=1,
        night_min_staff=2,
        rules=RULES,
    )
    assert staff[0] == 2
    assert staff[MONDAY_TEN] == 4


def test_night_window_follows_the_rules_given() -> None:
    shifted = LaborRules(night_start=23, night_end=7)
    load, floored = zero_night_load(weekly_load(_product_week(1, 4.0)).load, shifted)
    assert load[22] == 4.0
    assert load[23] == 0.0
    assert load[6] == 0.0
    assert load[7] == 4.0
    assert floored == 7 * 8


def test_zero_night_load_rejects_wrong_length() -> None:
    with pytest.raises(ValueError, match="entries"):
        zero_night_load((1.0,) * 23, RULES)


def test_result_does_not_depend_on_row_order() -> None:
    rows = _product_week(1, 4.0, weeks=2, stockout=frozenset({(0, MONDAY_TEN)}), stockout_sale=9.0)
    assert weekly_load(rows) == weekly_load(list(reversed(rows)))


@pytest.mark.parametrize(
    ("hours_sale", "hours_stock_status", "message"),
    [
        ((1.0,) * 23, (0,) * 24, "entries"),
        ((1.0,) * 24, (0,) * 23, "entries"),
        ((-1.0,) + (1.0,) * 23, (0,) * 24, "non-negative"),
        ((1.0,) * 24, (2,) + (0,) * 23, "0 or 1"),
    ],
)
def test_product_day_rejects_bad_input(
    hours_sale: tuple[float, ...], hours_stock_status: tuple[int, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        ProductDay(1, START, hours_sale, hours_stock_status)


def test_rejects_missing_weekday() -> None:
    rows = [row for row in _product_week(1, 4.0) if row.weekday != 6]
    with pytest.raises(ValueError, match="weekday"):
        weekly_load(rows)


def test_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one"):
        weekly_load([])
