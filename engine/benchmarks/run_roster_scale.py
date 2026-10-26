import argparse
import random
import time

from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import validate

SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def weekly_instance(employee_count: int, seed: int) -> Instance:
    """Seeded weekly demand: a daytime peak on top of a small overnight floor. Only the seed and
    the employee count vary between runs, so every row of the table is reproducible."""
    rng = random.Random(seed)
    demand = [0] * HOURS_PER_WEEK
    for day in range(7):
        for hour in range(24):
            peak = 3 if 8 <= hour < 20 else 1
            demand[hour_of_week(day, hour)] = peak + rng.randint(0, 1)
    employees = tuple(Employee(f"e{index:02d}", 100) for index in range(employee_count))
    return Instance(demand=tuple(demand), employees=employees, shift_types=SHIFTS)


def main(sizes: list[int], time_limit: float, seed: int, symmetry: bool) -> None:
    """Solve one weekly roster per employee count and print one row each: status, objective,
    bound, gap, wall time, shortfall hours and hard violations (must be 0). Run with the same
    seed and time limit to compare symmetry breaking on and off."""
    params = SolveParams(time_limit_seconds=time_limit, num_workers=1, random_seed=seed)
    print("employees,status,objective,bound,gap,wall_s,understaffed,violations,symmetry")
    for employee_count in sizes:
        instance = weekly_instance(employee_count, seed)
        started = time.perf_counter()
        outcome = solve_roster(instance, params, symmetry_breaking=symmetry)
        elapsed = time.perf_counter() - started
        violations = len(validate(instance, outcome.solution))
        result = outcome.result
        print(
            f"{employee_count},{result.status},{result.objective},{result.bound},{result.gap},"
            f"{elapsed:.2f},{outcome.understaffed_hours},{violations},{symmetry}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly roster scale check")
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 30, 40])
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-symmetry", action="store_true")
    args = parser.parse_args()
    main(args.sizes, args.time_limit, args.seed, symmetry=not args.no_symmetry)
