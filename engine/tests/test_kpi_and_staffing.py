import math

import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.kpi import (
    compute_kpi,
    labor_cost,
    labor_cost_share,
    night_premium_cost,
    staff_by_hour,
)
from shiftopt.staffing.linear import required_staff
from shiftopt.time_grid import HOURS_PER_WEEK, is_night_hour

RULES = LaborRules()


def flat_values(value: float = 0.0) -> list[float]:
    return [value] * HOURS_PER_WEEK


@pytest.mark.parametrize(
    ("load", "alpha", "productivity", "message"),
    [
        (flat_values()[:167], 1.0, 1.0, "168"),
        (flat_values(), 0.0, 1.0, "alpha"),
        (flat_values(), 1.0, 0.0, "productivity"),
        ([-1.0, *flat_values()[1:]], 1.0, 1.0, "non-negative"),
        ([math.nan, *flat_values()[1:]], 1.0, 1.0, "finite"),
    ],
)
def test_required_staff_rejects_bad_input(
    load: list[float], alpha: float, productivity: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        required_staff(load, alpha, productivity, 1, 1, RULES)


def test_required_staff_never_below_floor() -> None:
    load = [float(hour % 5) for hour in range(HOURS_PER_WEEK)]
    staff = required_staff(load, 1.0, 1.0, 2, 3, RULES)
    for hour, count in enumerate(staff):
        floor = 3 if is_night_hour(hour, RULES.night_start, RULES.night_end) else 2
        assert count >= floor


def test_required_staff_does_not_decrease_with_alpha() -> None:
    load = [float(hour) for hour in range(HOURS_PER_WEEK)]
    before = required_staff(load, 0.5, 1.0, 1, 1, RULES)
    after = required_staff(load, 1.5, 1.0, 1, 1, RULES)
    assert all(high >= low for high, low in zip(after, before, strict=True))


KPI_DAY = ShiftType("day", 8)
MIDNIGHT = ShiftType("midnight", 0)
LATE = ShiftType("late", 22)
EVENING = ShiftType("evening", 16)


def kpi_instance(demand_value: int = 1, employees: tuple[str, ...] = ("e1",)) -> Instance:
    return Instance(
        demand=(demand_value,) * HOURS_PER_WEEK,
        employees=tuple(Employee(name, 100) for name in employees),
        shift_types=(KPI_DAY, MIDNIGHT, LATE, EVENING),
    )


def test_kpi_for_single_day_shift() -> None:
    kpi = compute_kpi(kpi_instance(), Solution((Assignment("e1", 0, "day"),)))
    assert kpi.coverage_ratio == pytest.approx(8 / 168)
    assert kpi.understaffed_hours == 160
    assert kpi.overstaffed_hours == 0
    assert kpi.schedule_efficiency == pytest.approx(21)
    assert kpi.labor_cost == 100 * 800


def test_shift_counts_every_hour_it_covers() -> None:
    staff = staff_by_hour(kpi_instance(), Solution((Assignment("e1", 0, "day"),)))
    assert [hour for hour, count in enumerate(staff) if count] == list(range(8, 16))


def test_night_premium_is_added_to_cost() -> None:
    instance = kpi_instance(demand_value=0)
    solution = Solution((Assignment("e1", 0, "midnight"),))
    assert labor_cost(instance, solution) == 100 * (800 + 30 * 6)
    assert night_premium_cost(instance, solution) == 100 * 30 * 6


def test_ratios_use_one_when_denominator_is_zero() -> None:
    idle = compute_kpi(kpi_instance(demand_value=0), Solution((Assignment("e1", 0, "day"),)))
    assert idle.coverage_ratio == 1.0
    assert idle.schedule_efficiency == 0.0
    assert idle.overstaffed_hours == 8

    empty = compute_kpi(kpi_instance(), Solution(()))
    assert empty.coverage_ratio == 0.0
    assert empty.schedule_efficiency == 1.0


def test_staff_by_hour_wraps_overnight_shift_into_monday() -> None:
    staff = staff_by_hour(kpi_instance(), Solution((Assignment("e1", 6, "late"),)))
    assert [hour for hour, count in enumerate(staff) if count] == [0, 1, 2, 3, 4, 5, 166, 167]


def test_fairness_counts_night_and_weekend_shifts() -> None:
    instance = kpi_instance(employees=("e1", "e2"))
    solution = Solution(
        (
            Assignment("e1", 0, "late"),
            Assignment("e1", 1, "late"),
            Assignment("e1", 2, "evening"),
            Assignment("e2", 5, "evening"),
        )
    )
    kpi = compute_kpi(instance, solution)
    assert kpi.night_shift_stddev == pytest.approx(1.0)
    assert kpi.weekend_shift_stddev == pytest.approx(0.5)


def test_labor_cost_share_divides_by_assumed_revenue() -> None:
    assert labor_cost_share(80_000, 100_000) == pytest.approx(0.8)
    with pytest.raises(ValueError, match="revenue"):
        labor_cost_share(80_000, 0)
