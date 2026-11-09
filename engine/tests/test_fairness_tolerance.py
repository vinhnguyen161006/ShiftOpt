from collections.abc import Callable
from dataclasses import replace

import pytest

from shiftopt.constraints.fairness import worked_hours_spread
from shiftopt.domain import Assignment, Employee, Instance, RepairSpec, ShiftType, Solution
from shiftopt.kpi import compute_kpi
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.models.roster_mip import solve_roster_mip
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK
from shiftopt.validation import validate

InstanceFactory = Callable[..., Instance]
SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))
BASE = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)


def night_heavy_instance() -> Instance:
    demand = tuple(1 if hour % 24 < 6 else 0 for hour in range(HOURS_PER_WEEK))
    employees = tuple(Employee(f"e{index}", wage) for index, wage in enumerate((100, 120, 150)))
    return Instance(demand=demand, employees=employees, shift_types=SHIFTS)


def test_worked_hours_spread_counts_full_shift_lengths() -> None:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(Employee("e0", 100), Employee("e1", 100), Employee("e2", 100)),
        shift_types=SHIFTS,
    )
    solution = Solution(
        (
            Assignment("e0", 0, "day"),
            Assignment("e0", 1, "day"),
            Assignment("e2", 2, "night"),
        )
    )

    assert worked_hours_spread(instance, solution) == 16
    assert compute_kpi(instance, solution).hours_spread == 16


def test_zero_tolerance_has_no_hours_tier_and_three_tiers() -> None:
    outcome = solve_roster(night_heavy_instance(), BASE)

    assert outcome.hours_spread is None
    assert len(outcome.phases) == 3


def test_tolerance_lowers_night_spread_within_cost_bound() -> None:
    instance = night_heavy_instance()
    strict = solve_roster(instance, BASE)
    relaxed = solve_roster(instance, replace_tolerance(10.0))

    assert strict.night_spread is not None
    assert relaxed.night_spread is not None
    assert relaxed.night_spread < strict.night_spread
    assert relaxed.hours_spread is not None
    assert validate(instance, relaxed.solution) == []
    strict_cost = compute_kpi(instance, strict.solution).labor_cost
    relaxed_cost = compute_kpi(instance, relaxed.solution).labor_cost
    assert relaxed_cost <= strict_cost * 110 // 100


def test_relaxed_roster_keeps_full_coverage() -> None:
    instance = night_heavy_instance()
    strict = solve_roster(instance, BASE)
    relaxed = solve_roster(instance, replace_tolerance(10.0))

    assert relaxed.understaffed_hours == strict.understaffed_hours == 0


def test_mip_and_cpsat_agree_on_relaxed_cost_and_night_spread() -> None:
    instance = night_heavy_instance()
    params = replace_tolerance(5.0)

    cpsat = solve_roster(instance, params)
    mip = solve_roster_mip(instance, params)

    assert cpsat.result.status is SolveStatus.OPTIMAL
    assert mip.result.status is SolveStatus.OPTIMAL
    assert mip.phases[1].objective == cpsat.phases[1].objective
    assert mip.night_spread == cpsat.night_spread
    assert validate(instance, mip.solution) == []


def test_repair_with_all_days_locked_keeps_baseline_under_tolerance(
    build_instance: InstanceFactory,
) -> None:
    instance = build_instance(demand_per_hour=1, employee_count=3)
    baseline = solve_roster(instance, BASE).solution

    outcome = solve_roster(
        instance, replace_tolerance(5.0), repair=RepairSpec(baseline, from_day=7)
    )

    assert outcome.solution == baseline
    assert outcome.changes == 0


@pytest.mark.parametrize("tolerance", [-0.5, 10.5])
def test_tolerance_outside_range_is_rejected(tolerance: float) -> None:
    with pytest.raises(ValueError, match="cost_tolerance_percent"):
        SolveParams(cost_tolerance_percent=tolerance)


def replace_tolerance(tolerance: float) -> SolveParams:
    return replace(BASE, cost_tolerance_percent=tolerance)
