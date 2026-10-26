import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY, HOURS_PER_WEEK, is_night_hour

LATENT_DEMAND_METHOD = (
    "stockout hours replaced by the mean sale of the same product, weekday and hour over "
    "non-stockout days; a cell with no non-stockout day keeps its observed sale; "
    "each hour is the mean over days of the weekly sum across products"
)


@dataclass(frozen=True)
class ProductDay:
    """One product on one calendar day: 24 hourly sales and 24 stockout flags (1 = out of stock).
    Sales are normalized by the dataset source and are not staffing demand."""

    product_id: int
    day: date
    hours_sale: tuple[float, ...]
    hours_stock_status: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.hours_sale) != HOURS_PER_DAY or len(self.hours_stock_status) != HOURS_PER_DAY:
            raise ValueError(f"hours_sale and hours_stock_status must have {HOURS_PER_DAY} entries")
        if any(not math.isfinite(sale) or sale < 0 for sale in self.hours_sale):
            raise ValueError("hours_sale values must be finite and non-negative")
        if any(flag not in (0, 1) for flag in self.hours_stock_status):
            raise ValueError("hours_stock_status values must be 0 or 1")

    @property
    def weekday(self) -> int:
        return self.day.weekday()


@dataclass(frozen=True)
class WeeklyLoad:
    """load[d * 24 + h] is the mean normalized sales of hour h on weekday d, before the night
    floor. imputed_cells counts stockout cells replaced by a mean; unimputed_cells counts stockout
    cells with no non-stockout day to learn from, which keep their observed value."""

    load: tuple[float, ...]
    imputed_cells: int
    unimputed_cells: int
    method: str = LATENT_DEMAND_METHOD


def weekly_load(rows: Iterable[ProductDay]) -> WeeklyLoad:
    """Build the 168-hour load index of one store. Each stockout cell takes the mean of the same
    product's non-stockout sales at that weekday and hour. Hours are summed over products, then
    averaged over the days of each weekday. Night hours are kept here; zero_night_load applies the
    night rule when the caller quantifies the demand."""
    days = tuple(rows)
    if not days:
        raise ValueError("at least one product day is required")
    means = _non_stockout_means(days)
    totals = [0.0] * HOURS_PER_WEEK
    dates: dict[int, set[date]] = defaultdict(set)
    imputed = 0
    unimputed = 0
    for row in days:
        dates[row.weekday].add(row.day)
        for hour, (sale, flag) in enumerate(
            zip(row.hours_sale, row.hours_stock_status, strict=True)
        ):
            value = sale
            if flag:
                key = (row.product_id, row.weekday, hour)
                if key in means:
                    value = means[key]
                    imputed += 1
                else:
                    unimputed += 1
            totals[row.weekday * HOURS_PER_DAY + hour] += value
    missing = [weekday for weekday in range(DAYS_PER_WEEK) if weekday not in dates]
    if missing:
        raise ValueError(f"every weekday needs at least one day, missing weekdays: {missing}")
    load = tuple(total / len(dates[index // HOURS_PER_DAY]) for index, total in enumerate(totals))
    return WeeklyLoad(load, imputed, unimputed)


def zero_night_load(load: tuple[float, ...], rules: LaborRules) -> tuple[tuple[float, ...], int]:
    """Set night hours of a weekly load to zero, because sales do not describe night work
    (CLAUDE.md rule 7). Night hours follow rules.night_start and rules.night_end, so the night
    head count comes from the caller's rules. Returns the load and the number of night cells
    that had positive sales before being zeroed."""
    if len(load) != HOURS_PER_WEEK:
        raise ValueError(f"load must have {HOURS_PER_WEEK} entries")
    floored = sum(
        1
        for index, value in enumerate(load)
        if value > 0 and is_night_hour(index % HOURS_PER_DAY, rules.night_start, rules.night_end)
    )
    zeroed = tuple(
        0.0 if is_night_hour(index % HOURS_PER_DAY, rules.night_start, rules.night_end) else value
        for index, value in enumerate(load)
    )
    return zeroed, floored


def _non_stockout_means(days: tuple[ProductDay, ...]) -> dict[tuple[int, int, int], float]:
    sums: dict[tuple[int, int, int], float] = defaultdict(float)
    counts: dict[tuple[int, int, int], int] = defaultdict(int)
    for row in days:
        for hour, (sale, flag) in enumerate(
            zip(row.hours_sale, row.hours_stock_status, strict=True)
        ):
            if not flag:
                key = (row.product_id, row.weekday, hour)
                sums[key] += sale
                counts[key] += 1
    return {key: sums[key] / counts[key] for key in counts}
