from collections.abc import Sequence

from shiftopt.constraints.labor_law_vn import LaborRules


def required_staff(
    load: Sequence[float],
    alpha: float,
    productivity: float,
    min_staff: int,
    night_min_staff: int,
    rules: LaborRules,
) -> tuple[int, ...]:
    """TODO: convert an hourly load index into head count, per hour h:
    max(floor_h, ceil(alpha * load_h / productivity)).

    alpha de-normalizes the dataset scale and productivity is units handled per employee-hour;
    both are team assumptions exposed to the UI. floor_h is night_min_staff in night hours,
    min_staff otherwise. Reject a load that is not 168 entries and non-positive alpha or
    productivity.
    """
    raise NotImplementedError
