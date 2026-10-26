from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import ShiftType
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY


def rest_hours(prev: ShiftType, nxt: ShiftType, day_offset: int) -> int:
    """Hours of rest from the end of prev to the start of nxt, when nxt starts day_offset days
    after prev. Uses the general formula 24 * day_offset + sigma' - (sigma + L) from Section 5.3,
    not the L = 8 shortcut sigma - sigma' > 4."""
    return HOURS_PER_DAY * day_offset + nxt.start_hour - (prev.start_hour + prev.length)


def forbidden_shift_pairs(
    shift_types: tuple[ShiftType, ...], rules: LaborRules
) -> list[tuple[str, str, int]]:
    """Every (prev name, next name, day_offset) with day_offset in 1 to 6 whose rest is below
    min_rest_between_shifts (Article 110). The cyclic week makes offsets wrap, so a shift on
    Sunday and one on Monday are offset 1 apart as well. The pair (14h-22h, 06h-14h) at offset 1
    is always in the result."""
    return [
        (prev.name, nxt.name, offset)
        for prev in shift_types
        for nxt in shift_types
        for offset in range(1, DAYS_PER_WEEK)
        if rest_hours(prev, nxt, offset) < rules.min_rest_between_shifts
    ]


def consecutive_day_windows(rules: LaborRules) -> list[tuple[int, ...]]:
    """Cyclic windows of max_consecutive_days + 1 day indexes, one starting at each day of the
    week. Every window must hold at least one day off (Article 105 and the consecutive-day rule).
    Empty when the window is longer than the week."""
    size = rules.max_consecutive_days + 1
    if size > DAYS_PER_WEEK:
        return []
    return [
        tuple((start + offset) % DAYS_PER_WEEK for offset in range(size))
        for start in range(DAYS_PER_WEEK)
    ]
