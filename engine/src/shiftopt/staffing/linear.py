"""Linear conversion of an hourly load index into required head count (retail mode).

alpha and productivity are team assumptions, not facts from the data, and must be shown on the UI.
The default values below are placeholders pending decision 0.1 in WORKLOG.md.
"""

import math
from collections.abc import Sequence

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import HOURS_PER_WEEK, is_night_hour

DEFAULT_ALPHA = 1.0
DEFAULT_PRODUCTIVITY = 1.0
DEFAULT_MIN_STAFF = 1
DEFAULT_NIGHT_MIN_STAFF = 1
CEIL_TOLERANCE_DIGITS = 9


def tolerant_ceil(value: float) -> int:
    """Ceiling that ignores floating point noise, so 0.1 * 30 counts as 3 and not 4."""
    return math.ceil(round(value, CEIL_TOLERANCE_DIGITS))


def required_staff(
    load: Sequence[float],
    alpha: float,
    productivity: float,
    min_staff: int,
    night_min_staff: int,
    rules: LaborRules,
) -> tuple[int, ...]:
    """Convert an hourly load index into head count, per hour h:
    max(floor_h, ceil(alpha * load_h / productivity)).

    alpha de-normalizes the dataset scale and productivity is units handled per employee-hour.
    floor_h is night_min_staff in night hours (Article 106 window from rules), min_staff otherwise;
    night demand is a fixed floor because sales data does not describe night work.
    """
    if len(load) != HOURS_PER_WEEK:
        raise ValueError(f"load must have {HOURS_PER_WEEK} entries")
    if any(not math.isfinite(value) or value < 0 for value in load):
        raise ValueError("load values must be finite and non-negative")
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    if productivity <= 0:
        raise ValueError("productivity must be positive")
    if min_staff < 0 or night_min_staff < 0:
        raise ValueError("staff floors must be non-negative")
    return tuple(
        max(
            night_min_staff
            if is_night_hour(hour, rules.night_start, rules.night_end)
            else min_staff,
            tolerant_ceil(alpha * value / productivity),
        )
        for hour, value in enumerate(load)
    )
