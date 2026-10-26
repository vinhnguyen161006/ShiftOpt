"""Synthetic hourly call arrivals for the call-centre mode. The shape is an assumption, not observed
data: a weekday factor, a daily shape with peaks, and seeded multiplicative noise."""

import math
import random
from collections.abc import Sequence

from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY, HOURS_PER_WEEK

DEFAULT_WEEKDAY_FACTORS = (1.0, 1.0, 1.0, 1.0, 1.1, 1.3, 1.2)
DEFAULT_PEAK_HOURS = (11.0, 19.0)
DEFAULT_PEAK_WIDTH = 2.5
OFF_PEAK_SHARE = 0.2


def simulate_arrival_rates(
    base_rate: float,
    weekday_factors: Sequence[float] = DEFAULT_WEEKDAY_FACTORS,
    peak_hours: Sequence[float] = DEFAULT_PEAK_HOURS,
    peak_width: float = DEFAULT_PEAK_WIDTH,
    noise: float = 0.0,
    seed: int = 0,
) -> tuple[float, ...]:
    """Calls per hour over the 168-hour week: base_rate * weekday factor * daily shape, where the
    shape is OFF_PEAK_SHARE plus a Gaussian bump at each peak hour, multiplied by
    (1 + noise * N(0, 1)) and cut at zero. The same seed always gives the same week."""
    _check_inputs(base_rate, weekday_factors, peak_hours, peak_width, noise)
    generator = random.Random(seed)
    rates: list[float] = []
    for index in range(HOURS_PER_WEEK):
        weekday, hour = divmod(index, HOURS_PER_DAY)
        shape = OFF_PEAK_SHARE + sum(
            math.exp(-(_circular_distance(hour, peak) ** 2) / (2 * peak_width**2))
            for peak in peak_hours
        )
        jitter = 1 + noise * generator.gauss(0.0, 1.0)
        rates.append(max(0.0, base_rate * weekday_factors[weekday] * shape * jitter))
    return tuple(rates)


def _circular_distance(hour: int, peak: float) -> float:
    distance = abs(hour - peak)
    return min(distance, HOURS_PER_DAY - distance)


def _check_inputs(
    base_rate: float,
    weekday_factors: Sequence[float],
    peak_hours: Sequence[float],
    peak_width: float,
    noise: float,
) -> None:
    if not math.isfinite(base_rate) or base_rate < 0:
        raise ValueError("base_rate must be finite and non-negative")
    if len(weekday_factors) != DAYS_PER_WEEK or any(
        not math.isfinite(factor) or factor <= 0 for factor in weekday_factors
    ):
        raise ValueError(f"weekday_factors must be {DAYS_PER_WEEK} positive finite values")
    if any(not 0 <= peak < HOURS_PER_DAY for peak in peak_hours):
        raise ValueError(f"peak_hours must lie in [0, {HOURS_PER_DAY})")
    if peak_width <= 0:
        raise ValueError("peak_width must be positive")
    if noise < 0:
        raise ValueError("noise must be non-negative")
