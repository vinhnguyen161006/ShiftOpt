import math
from fractions import Fraction

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
from shiftopt.staffing.erlang import (
    erlang_c_service_level,
    erlang_c_wait_probability,
    required_staff_erlang_c,
    required_staff_square_root,
)
from shiftopt.staffing.linear import required_staff
from shiftopt.time_grid import HOURS_PER_WEEK, is_night_hour

RULES = LaborRules()
HANDLE_SECONDS = 180.0
ANSWER_SECONDS = 20.0


def flat_values(value: float = 0.0) -> list[float]:
    return [value] * HOURS_PER_WEEK


def erlang_c_wait_probability_exact(agents: int, offered_load: int) -> float:
    """Oracle: direct Erlang C sum in exact rationals, independent of the Erlang B recursion."""
    load = Fraction(offered_load)
    below = sum(load**k / math.factorial(k) for k in range(agents))
    queued = load**agents / math.factorial(agents) * Fraction(agents) / (agents - load)
    return float(queued / (below + queued))


def test_required_staff_applies_ceil_and_floors() -> None:
    load = flat_values()
    load[10] = 2.5
    load[23] = 0.0
    staff = required_staff(load, 2.0, 1.0, 1, 3, RULES)
    assert staff[10] == 5
    assert staff[11] == 1
    assert staff[23] == 3


def test_required_staff_ignores_float_noise_before_ceil() -> None:
    staff = required_staff(flat_values(30.0), 0.1, 1.0, 0, 0, RULES)
    assert staff[10] == 3


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


@pytest.mark.parametrize("agents", [11, 12, 13, 14, 15])
def test_erlang_c_wait_probability_matches_exact_sum(agents: int) -> None:
    assert erlang_c_wait_probability(agents, 10.0) == pytest.approx(
        erlang_c_wait_probability_exact(agents, 10), rel=1e-12
    )


def test_erlang_c_stays_finite_for_large_pools() -> None:
    probability = erlang_c_wait_probability(2100, 2000.0)
    assert math.isfinite(probability)
    assert 0 < probability < 1


def test_erlang_c_rejects_unstable_queue() -> None:
    with pytest.raises(ValueError, match="offered load"):
        erlang_c_wait_probability(10, 10.0)


def test_required_staff_erlang_c_returns_minimum_agents_for_target() -> None:
    rates = flat_values()
    rates[10] = 200.0
    staff = required_staff_erlang_c(rates, HANDLE_SECONDS, 0.8, ANSWER_SECONDS, 1)
    agents = staff[10]
    assert erlang_c_service_level(agents, 10.0, HANDLE_SECONDS, ANSWER_SECONDS) >= 0.8
    assert erlang_c_service_level(agents - 1, 10.0, HANDLE_SECONDS, ANSWER_SECONDS) < 0.8


def test_required_staff_erlang_c_uses_minimum_for_idle_hours() -> None:
    staff = required_staff_erlang_c(flat_values(), HANDLE_SECONDS, 0.8, ANSWER_SECONDS, 2)
    assert staff == (2,) * HOURS_PER_WEEK


def test_required_staff_erlang_c_does_not_decrease_with_load() -> None:
    low = required_staff_erlang_c(flat_values(100.0), HANDLE_SECONDS, 0.8, ANSWER_SECONDS, 1)
    high = required_staff_erlang_c(flat_values(200.0), HANDLE_SECONDS, 0.8, ANSWER_SECONDS, 1)
    assert all(after >= before for after, before in zip(high, low, strict=True))


@pytest.mark.parametrize(
    ("values", "handle_seconds", "target", "message"),
    [
        (flat_values()[:167], HANDLE_SECONDS, 0.8, "168"),
        (flat_values(), 0.0, 0.8, "handle_seconds"),
        (flat_values(), HANDLE_SECONDS, 1.0, "target_service_level"),
        ([-1.0, *flat_values()[1:]], HANDLE_SECONDS, 0.8, "non-negative"),
    ],
)
def test_required_staff_erlang_c_rejects_bad_input(
    values: list[float], handle_seconds: float, target: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        required_staff_erlang_c(values, handle_seconds, target, ANSWER_SECONDS, 1)


def test_square_root_staffing_matches_formula() -> None:
    rates = flat_values()
    rates[10] = 200.0
    assert required_staff_square_root(rates, HANDLE_SECONDS, 1.0, 1)[10] == 14
    assert required_staff_square_root(rates, HANDLE_SECONDS, 0.0, 1)[10] == 10


def test_square_root_staffing_uses_minimum_for_idle_hours() -> None:
    assert required_staff_square_root(flat_values(), HANDLE_SECONDS, 1.0, 1)[0] == 1


def test_square_root_staffing_rejects_negative_beta() -> None:
    with pytest.raises(ValueError, match="beta"):
        required_staff_square_root(flat_values(), HANDLE_SECONDS, -0.5, 1)


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
