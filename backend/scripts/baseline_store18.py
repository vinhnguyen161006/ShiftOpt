import argparse
import time
from pathlib import Path

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.kpi import compute_kpi
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams
from shiftopt.validation import validate

from src.config import get_settings
from src.demand.dataset_loader import dataset_required_staff
from src.demand.schemas import ConversionParams

SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))
ALPHA = 1.0
PRODUCTIVITY = 4.0
MIN_STAFF = 1
NIGHT_MIN_STAFF = 1


def baseline_instance(store_id: int, employee_count: int, productivity: float) -> Instance:
    """Store demand under the team's assumed conversion (alpha, p and staff floors from the
    constants above), with night hours set to the night floor by dataset_required_staff."""
    conversion = ConversionParams(
        alpha=ALPHA,
        productivity=productivity,
        min_staff=MIN_STAFF,
        night_min_staff=NIGHT_MIN_STAFF,
    )
    demand = dataset_required_staff(
        Path(get_settings().dataset_dir), store_id, conversion, LaborRules()
    )
    employees = tuple(Employee(f"e{index:02d}", 100) for index in range(employee_count))
    return Instance(
        demand=demand.required_staff,
        employees=employees,
        shift_types=SHIFTS,
    )


def main(
    store_id: int,
    employee_count: int,
    productivity: float,
    time_limit: float,
    workers: int,
    seeds: list[int],
) -> None:
    """One CSV row per seed: status, objective, bound, gap, wall time, understaffed hours,
    coverage ratio, hard violations (must be 0) and solver version. Same seed with one worker
    reproduces a row."""
    print(
        "store,employees,productivity,seed,workers,status,objective,bound,gap,wall_s,"
        "understaffed,coverage,violations,solver"
    )
    instance = baseline_instance(store_id, employee_count, productivity)
    for seed in seeds:
        params = SolveParams(
            time_limit_seconds=time_limit,
            relative_gap_limit=0.01,
            num_workers=workers,
            random_seed=seed,
        )
        started = time.perf_counter()
        outcome = solve_roster(instance, params)
        elapsed = time.perf_counter() - started
        violations = len(validate(instance, outcome.solution))
        coverage = compute_kpi(instance, outcome.solution).coverage_ratio
        result = outcome.result
        print(
            f"{store_id},{employee_count},{productivity},{seed},{workers},{result.status},"
            f"{result.objective},{result.bound},{result.gap},{elapsed:.2f},"
            f"{outcome.understaffed_hours},{coverage:.4f},{violations},{result.solver}"
            f" {result.solver_version}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline scenario on one FreshRetailNet store")
    parser.add_argument("--store", type=int, default=18)
    parser.add_argument("--employees", type=int, default=30)
    parser.add_argument("--productivity", type=float, default=PRODUCTIVITY)
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    args = parser.parse_args()
    main(
        args.store,
        args.employees,
        args.productivity,
        args.time_limit,
        args.workers,
        args.seeds,
    )
