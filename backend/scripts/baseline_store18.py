import argparse
import time
from pathlib import Path

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.kpi import compute_kpi
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams
from shiftopt.validation import validate

from src.demand.sales_ingest import derive_demand
from src.demand.schemas import ConversionParams, SalesMapping

ROOT = Path(__file__).resolve().parents[2]
TRAIN_FILE = ROOT / "data" / "demo" / "train.parquet"
FRESHRETAILNET_MAPPING = {
    "date_column": "dt",
    "sales_column": "hours_sale",
    "stockout_column": "hours_stock_status",
    "product_column": "product_id",
    "store_column": "store_id",
}

SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))
ALPHA = 1.0
PRODUCTIVITY = 4.0
MIN_STAFF = 1
NIGHT_MIN_STAFF = 1
MODES = ("exact", "decompose")
CSV_HEADER = (
    "store,employees,productivity,seed,workers,mode,time_limit,status,objective,bound,gap,"
    "wall_s,understaffed,coverage,violations,capacity_ratio,shortfall_status,shortfall_bound,"
    "coverage_upper,approximate,solver"
)


def baseline_instance(store_id: int, employee_count: int, productivity: float) -> Instance:
    """Store demand under the team's assumed conversion (alpha, p and staff floors from the
    constants above), with night hours set to the night floor."""
    mapping = SalesMapping(**FRESHRETAILNET_MAPPING, store=str(store_id))
    conversion = ConversionParams(
        alpha=ALPHA,
        productivity=productivity,
        min_staff=MIN_STAFF,
        night_min_staff=NIGHT_MIN_STAFF,
    )
    demand = derive_demand(
        TRAIN_FILE.read_bytes(), mapping, conversion, LaborRules(), sha256="baseline"
    )
    employees = tuple(Employee(f"e{index:02d}", 100) for index in range(employee_count))
    return Instance(
        demand=demand.required_staff,
        employees=employees,
        shift_types=SHIFTS,
    )


def main(
    store_id: int,
    employee_counts: list[int],
    productivity: float,
    time_limits: list[float],
    modes: list[str],
    workers: int,
    seeds: list[int],
) -> None:
    """One CSV row per (employees, time limit, mode, seed). capacity_ratio is staffed hours at
    the weekly maximum over total demand hours. shortfall_status and shortfall_bound come from
    the first lexicographic tier (understaffed hours); coverage_upper = 1 - shortfall_bound /
    total demand is the coverage the solver proves it cannot exceed. Decompose rows are
    approximate and never OPTIMAL. Same seed with one worker reproduces a row."""
    print(CSV_HEADER)
    for employee_count in employee_counts:
        instance = baseline_instance(store_id, employee_count, productivity)
        total_demand = sum(instance.demand)
        capacity_ratio = employee_count * LaborRules().max_weekly_hours / total_demand
        for time_limit in time_limits:
            for mode in modes:
                for seed in seeds:
                    params = SolveParams(
                        time_limit_seconds=time_limit,
                        relative_gap_limit=0.01,
                        num_workers=workers,
                        random_seed=seed,
                    )
                    started = time.perf_counter()
                    outcome = solve_roster(instance, params, decompose=mode == "decompose")
                    elapsed = time.perf_counter() - started
                    violations = len(validate(instance, outcome.solution))
                    coverage = compute_kpi(instance, outcome.solution).coverage_ratio
                    result = outcome.result
                    tier = outcome.phases[0]
                    shortfall_bound = tier.bound
                    coverage_upper = (
                        None if shortfall_bound is None else 1 - shortfall_bound / total_demand
                    )
                    print(
                        f"{store_id},{employee_count},{productivity},{seed},{workers},{mode},"
                        f"{time_limit},{result.status},{result.objective},{result.bound},"
                        f"{result.gap},{elapsed:.2f},{outcome.understaffed_hours},"
                        f"{coverage:.4f},{violations},{capacity_ratio:.4f},{tier.status},"
                        f"{shortfall_bound},{coverage_upper},{outcome.approximate},"
                        f"{result.solver} {result.solver_version}"
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline scenario on one FreshRetailNet store")
    parser.add_argument("--store", type=int, default=18)
    parser.add_argument("--employees", type=int, nargs="+", default=[30])
    parser.add_argument("--productivity", type=float, default=PRODUCTIVITY)
    parser.add_argument("--time-limits", type=float, nargs="+", default=[60.0])
    parser.add_argument("--modes", choices=MODES, nargs="+", default=["exact"])
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    args = parser.parse_args()
    main(
        args.store,
        args.employees,
        args.productivity,
        args.time_limits,
        args.modes,
        args.workers,
        args.seeds,
    )
