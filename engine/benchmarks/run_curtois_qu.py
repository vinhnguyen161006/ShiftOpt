import argparse


def main(time_limit: float) -> None:
    """TODO: iterate over Instance1-5 from data/benchmarks/curtois_qu/, call
    shiftopt.models.roster_cpsat.solve_roster and print a table with columns:
    instance, published_bound, objective, gap, status, wall_time.

    Exit with code 1 if any result is INFEASIBLE or MODEL_INVALID so CI catches it.
    Each instance file must be downloaded separately if licensing does not allow commit.
    """
    raise NotImplementedError


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Curtois and Qu (2014) benchmark runner")
    parser.add_argument("--time-limit", type=float, default=120.0)
    args = parser.parse_args()
    main(args.time_limit)
