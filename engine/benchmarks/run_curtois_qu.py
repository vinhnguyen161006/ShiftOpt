import argparse
import csv
import sys
from pathlib import Path

from shiftopt.benchmarks.curtois_qu import parse_instance, solve_benchmark
from shiftopt.solvers.base import SolveParams, SolveStatus

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "curtois_qu"
PUBLISHED_OPTIMUM = {
    "Instance1": 607,
    "Instance2": 828,
    "Instance3": 1001,
    "Instance4": 1716,
    "Instance5": 1143,
}
FAILED_STATUSES = (SolveStatus.INFEASIBLE, SolveStatus.UNKNOWN)
COLUMNS = (
    "instance",
    "published",
    "objective",
    "bound",
    "gap_to_published",
    "status",
    "wall_s",
    "time_limit_s",
    "workers",
    "seed",
)


def main(time_limit: float, workers: int, seed: int) -> int:
    """Solve Instance1-5 with the exact CP-SAT model and print one CSV row each. Relative gap is
    0 so a row claims OPTIMAL only when the optimum is proven. Returns 1 when an instance file is
    missing or an instance yields no solution."""
    params = SolveParams(
        time_limit_seconds=time_limit,
        relative_gap_limit=0.0,
        num_workers=workers,
        random_seed=seed,
    )
    writer = csv.writer(sys.stdout)
    writer.writerow(COLUMNS)
    exit_code = 0
    for name, published in PUBLISHED_OPTIMUM.items():
        path = DATA_DIR / f"{name}.txt"
        if not path.exists():
            print(f"missing {path}: run engine/benchmarks/download_curtois_qu.py", file=sys.stderr)
            return 1
        instance = parse_instance(path.read_text(encoding="ascii"))
        result = solve_benchmark(instance, params)
        if result.status in FAILED_STATUSES:
            exit_code = 1
        gap_to_published = None if result.objective is None else result.objective - published
        writer.writerow(
            (
                name,
                published,
                result.objective,
                result.bound,
                gap_to_published,
                result.status,
                f"{result.wall_time_seconds:.2f}",
                time_limit,
                workers,
                seed,
            )
        )
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Curtois and Qu (2014) benchmark runner")
    parser.add_argument("--time-limit", type=float, default=120.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    raise SystemExit(main(args.time_limit, args.workers, args.seed))
