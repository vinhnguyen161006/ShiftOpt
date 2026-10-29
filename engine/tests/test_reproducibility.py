from collections.abc import Callable

from shiftopt.domain import Assignment, Employee, Instance, ShiftType
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.implicit_breaks_cpsat import solve_with_implicit_breaks_cpsat
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams
from shiftopt.time_grid import HOURS_PER_WEEK

PARAMS = SolveParams(time_limit_seconds=60, relative_gap_limit=0.0, num_workers=1, random_seed=0)
WAGE = 100
RUNS = 3
THREE_SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def _assignments(rows: tuple[Assignment, ...]) -> list[Assignment]:
    return sorted(rows, key=lambda row: (row.employee_id, row.day, row.shift_name))


def test_roster_repeats_objective_and_assignments() -> None:
    demand = [0] * HOURS_PER_WEEK
    for hour in range(8, 16):
        demand[hour] = 1
    employees = tuple(Employee(f"e{index}", WAGE) for index in range(2))
    instance = Instance(demand=tuple(demand), employees=employees, shift_types=THREE_SHIFTS)

    outcomes = [solve_roster(instance, PARAMS) for _ in range(RUNS)]

    first = outcomes[0]
    for outcome in outcomes[1:]:
        assert outcome.result.objective == first.result.objective
        assert _assignments(outcome.solution.assignments) == _assignments(
            first.solution.assignments
        )


def test_highs_aggregate_repeats_counts(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=2)

    outcomes = [solve_with_implicit_breaks(instance, WAGE, PARAMS) for _ in range(RUNS)]

    first = outcomes[0]
    for outcome in outcomes[1:]:
        assert outcome.result.objective == first.result.objective
        assert outcome.counts == first.counts


def test_cpsat_aggregate_repeats_counts(build_instance: Callable[..., Instance]) -> None:
    instance = build_instance(demand_per_hour=2)

    outcomes = [solve_with_implicit_breaks_cpsat(instance, WAGE, PARAMS) for _ in range(RUNS)]

    first = outcomes[0]
    for outcome in outcomes[1:]:
        assert outcome.result.objective == first.result.objective
        assert outcome.counts == first.counts
