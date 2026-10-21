from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import ShiftType


def forbidden_shift_pairs(
    shift_types: tuple[ShiftType, ...], rules: LaborRules
) -> list[tuple[str, str]]:
    """TODO: return all (prev_name, next_name) pairs that violate the minimum rest constraint.

    A pair is forbidden when 24 + next.start_hour - (prev.start_hour + prev.length) < min_rest,
    using the general formula from Section 5.3 (not the L=8 shortcut sigma - sigma' > 4).
    The pair (14h-22h shift, 06h-14h shift) must always appear in the result.
    """
    raise NotImplementedError


def consecutive_day_windows(rules: LaborRules) -> list[tuple[int, ...]]:
    """TODO: cyclic windows of max_consecutive_days + 1 day indexes, one starting at each day of
    the week; the roster model requires at least one day off in every window. Return an empty
    list when the window is longer than the week."""
    raise NotImplementedError
