import argparse
import random
import time
from collections.abc import Callable

from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.kpi import compute_kpi
from shiftopt.models.roster_cpsat import RosterOutcome, roster_model_size, solve_roster
from shiftopt.models.roster_mip import roster_model_size as mip_model_size
from shiftopt.models.roster_mip import solve_roster_mip
from shiftopt.solvers.base import SolveParams
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import validate

SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))
SIX_SHIFTS = tuple(ShiftType(f"s{start:02d}", start) for start in range(0, 24, 4))
SHIFT_SETS: dict[str, tuple[ShiftType, ...]] = {"3_shifts": SHIFTS, "6_shifts": SIX_SHIFTS}
MIP_SOLVER: Callable[[Instance, SolveParams], RosterOutcome] = solve_roster_mip


def weekly_instance(
    employee_count: int, seed: int, shifts: tuple[ShiftType, ...] = SHIFTS
) -> Instance:
    """Seeded weekly demand: a daytime peak on top of a small overnight floor. Only the seed and
    the employee count vary between runs, so every row of the table is reproducible."""
    rng = random.Random(seed)
    demand = [0] * HOURS_PER_WEEK
    for day in range(7):
        for hour in range(24):
            peak = 3 if 8 <= hour < 20 else 1
            demand[hour_of_week(day, hour)] = peak + rng.randint(0, 1)
    employees = tuple(Employee(f"e{index:02d}", 100) for index in range(employee_count))
    return Instance(demand=tuple(demand), employees=employees, shift_types=shifts)


def print_sizes(sizes: list[int]) -> None:
    print("employees,shifts,solver,variables,constraints")
    for shift_name, shifts in SHIFT_SETS.items():
        for employee_count in sizes:
            instance = weekly_instance(employee_count, 0, shifts)
            cp_vars, cp_rows = roster_model_size(instance)
            mip_vars, mip_rows = mip_model_size(instance)
            print(f"{employee_count},{shift_name},cpsat,{cp_vars},{cp_rows}")
            print(f"{employee_count},{shift_name},mip,{mip_vars},{mip_rows}")


def print_solves(
    sizes: list[int],
    solvers: list[str],
    time_limit: float,
    seeds: list[int],
    workers: int,
    symmetry: bool,
) -> None:
    """Solve one weekly roster per solver, employee count and seed, and print one CSV row each.
    shortfall_obj and cost_obj are the first two lexicographic tiers. violations must be 0. Same
    seed and one worker reproduce a row; more workers do not."""
    print(
        "employees,seed,solver,workers,status,objective,bound,gap,wall_s,understaffed,coverage,"
        "violations,shortfall_obj,cost_obj,symmetry"
    )
    for seed in seeds:
        for employee_count in sizes:
            instance = weekly_instance(employee_count, seed)
            for solver_name in solvers:
                params = SolveParams(
                    time_limit_seconds=time_limit,
                    relative_gap_limit=0.01,
                    num_workers=workers,
                    random_seed=seed,
                )
                started = time.perf_counter()
                if solver_name == "cpsat":
                    outcome = solve_roster(instance, params, symmetry_breaking=symmetry)
                else:
                    outcome = MIP_SOLVER(instance, params)
                elapsed = time.perf_counter() - started
                violations = len(validate(instance, outcome.solution))
                coverage = compute_kpi(instance, outcome.solution).coverage_ratio
                result = outcome.result
                tiers = outcome.phases
                shortfall = tiers[0].objective if tiers else None
                cost = tiers[1].objective if len(tiers) > 1 else None
                print(
                    f"{employee_count},{seed},{solver_name},{workers},{result.status},"
                    f"{result.objective},{result.bound},{result.gap},{elapsed:.2f},"
                    f"{outcome.understaffed_hours},{coverage:.4f},{violations},"
                    f"{shortfall},{cost},{symmetry}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly roster scale check")
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 30, 40])
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--symmetry", action="store_true")
    parser.add_argument("--solver", choices=["cpsat", "mip", "both"], default="cpsat")
    parser.add_argument("--sizes-only", action="store_true")
    args = parser.parse_args()
    if args.sizes_only:
        print_sizes(args.sizes)
    else:
        chosen = ["cpsat", "mip"] if args.solver == "both" else [args.solver]
        print_solves(args.sizes, chosen, args.time_limit, args.seeds, args.workers, args.symmetry)
