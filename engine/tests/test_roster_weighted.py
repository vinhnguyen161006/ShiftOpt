import pytest

from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.roster_cpsat import roster_model_size, solve_roster, solve_roster_weighted
from shiftopt.models.roster_mip import roster_model_size as mip_model_size
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def day_shift_instance(employee_count: int) -> Instance:
    return Instance(
        demand=tuple(1 if 8 <= hour < 16 else 0 for hour in range(HOURS_PER_WEEK)),
        employees=tuple(Employee(f"e{index}", 100) for index in range(employee_count)),
        shift_types=SHIFTS,
    )


def test_huge_shortfall_weight_matches_lexicographic_shortfall() -> None:
    instance = day_shift_instance(3)

    weighted = solve_roster_weighted(instance, PARAMS, shortfall_weight=10_000_000)
    lexicographic = solve_roster(instance, PARAMS)

    assert weighted.result.status is SolveStatus.OPTIMAL
    assert weighted.understaffed_hours == lexicographic.understaffed_hours
    assert validate(instance, weighted.solution) == []


def test_zero_shortfall_weight_can_leave_coverage_open_to_save_cost() -> None:
    instance = day_shift_instance(3)

    free = solve_roster_weighted(instance, PARAMS, shortfall_weight=0)
    covered = solve_roster_weighted(instance, PARAMS, shortfall_weight=10_000_000)

    assert free.result.objective is not None
    assert covered.result.objective is not None
    assert free.understaffed_hours is not None
    assert covered.understaffed_hours is not None
    assert free.understaffed_hours >= covered.understaffed_hours


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        solve_roster_weighted(day_shift_instance(2), PARAMS, shortfall_weight=-1)


def test_model_size_grows_with_employees() -> None:
    small = roster_model_size(day_shift_instance(2))
    large = roster_model_size(day_shift_instance(4))

    assert small[0] > 0
    assert small[1] > 0
    assert large[0] > small[0]
    assert large[1] > small[1]


def test_mip_model_size_grows_with_employees() -> None:
    small = mip_model_size(day_shift_instance(2))
    large = mip_model_size(day_shift_instance(4))

    assert large[0] > small[0]
    assert large[1] > small[1]
