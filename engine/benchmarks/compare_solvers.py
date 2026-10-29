import csv
import sys
from collections.abc import Callable

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.implicit_breaks_cpsat import solve_with_implicit_breaks_cpsat
from shiftopt.solvers.base import SolveParams, SolveResult
from shiftopt.time_grid import HOURS_PER_WEEK

WAGE = 100
EMPLOYEES = tuple(Employee(f"e{index}", WAGE) for index in range(40))
THREE_SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))
SPACED_SHIFTS = tuple(ShiftType(f"s{start:02d}", start) for start in range(0, 24, 3))
TIME_LIMITS = (10.0, 60.0)
SEED = 0


def uniform_instance() -> Instance:
    return Instance(
        demand=(1,) * HOURS_PER_WEEK,
        employees=EMPLOYEES,
        shift_types=THREE_SHIFTS,
        rules=LaborRules(),
    )


def peaked_demand() -> tuple[int, ...]:
    return tuple(2 if hour % 24 in range(8, 20) else 1 for hour in range(HOURS_PER_WEEK))


def peaked_instance() -> Instance:
    return Instance(
        demand=peaked_demand(),
        employees=EMPLOYEES,
        shift_types=THREE_SHIFTS,
        rules=LaborRules(),
    )


def spaced_instance() -> Instance:
    return Instance(
        demand=peaked_demand(),
        employees=EMPLOYEES,
        shift_types=SPACED_SHIFTS,
        rules=LaborRules(),
    )


INSTANCES: tuple[tuple[str, Callable[[], Instance]], ...] = (
    ("uniform_3_shifts", uniform_instance),
    ("peaked_3_shifts", peaked_instance),
    ("peaked_spaced_8_shifts", spaced_instance),
)
SOLVERS: tuple[tuple[str, Callable[[Instance, SolveParams], SolveResult]], ...] = (
    ("highs", lambda instance, params: solve_with_implicit_breaks(instance, WAGE, params).result),
    (
        "cpsat",
        lambda instance, params: solve_with_implicit_breaks_cpsat(instance, WAGE, params).result,
    ),
)


def main() -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(
        ("instance", "solver", "time_limit_s", "status", "objective", "bound", "gap", "wall_s")
    )
    for name, build in INSTANCES:
        instance = build()
        for time_limit in TIME_LIMITS:
            params = SolveParams(
                time_limit_seconds=time_limit,
                relative_gap_limit=0.0,
                num_workers=1,
                random_seed=SEED,
            )
            for solver_name, solve in SOLVERS:
                result = solve(instance, params)
                writer.writerow(
                    (
                        name,
                        solver_name,
                        time_limit,
                        result.status,
                        result.objective,
                        result.bound,
                        result.gap,
                        f"{result.wall_time_seconds:.2f}",
                    )
                )


if __name__ == "__main__":
    main()
