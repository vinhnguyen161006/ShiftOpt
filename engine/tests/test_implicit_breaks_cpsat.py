from collections.abc import Callable

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.implicit_breaks_cpsat import solve_with_implicit_breaks_cpsat
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK

PARAMS = SolveParams(num_workers=1, time_limit_seconds=30, relative_gap_limit=0.0)
WAGE = 100


def test_cpsat_matches_highs_uniform_demand(
    build_instance: Callable[..., Instance],
) -> None:
    instance = build_instance(demand_per_hour=1)

    highs = solve_with_implicit_breaks(instance, WAGE, PARAMS)
    cpsat = solve_with_implicit_breaks_cpsat(instance, WAGE, PARAMS)

    assert highs.result.status is SolveStatus.OPTIMAL
    assert cpsat.result.status is SolveStatus.OPTIMAL
    assert cpsat.result.objective == highs.result.objective


def test_cpsat_matches_highs_on_peaked_demand(three_shifts: tuple[ShiftType, ...]) -> None:
    demand = tuple(2 if hour % 24 in range(8, 20) else 1 for hour in range(HOURS_PER_WEEK))
    instance = Instance(
        demand=demand,
        employees=tuple(Employee(f"e{i}", WAGE) for i in range(6)),
        shift_types=three_shifts,
        rules=LaborRules(),
    )

    highs = solve_with_implicit_breaks(instance, WAGE, PARAMS)
    cpsat = solve_with_implicit_breaks_cpsat(instance, WAGE, PARAMS)

    assert highs.result.status is SolveStatus.OPTIMAL
    assert cpsat.result.status is SolveStatus.OPTIMAL
    assert cpsat.result.objective == highs.result.objective


def test_cpsat_returns_no_duals(build_instance: Callable[..., Instance]) -> None:
    cpsat = solve_with_implicit_breaks_cpsat(build_instance(demand_per_hour=1), WAGE, PARAMS)

    assert cpsat.duals is None
    assert all(value >= 0 for value in cpsat.counts.values())
