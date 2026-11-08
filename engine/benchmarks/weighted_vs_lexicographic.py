import csv
import sys

from benchmarks.run_roster_scale import weekly_instance
from shiftopt.domain import Instance
from shiftopt.kpi import compute_kpi
from shiftopt.models.roster_cpsat import RosterOutcome, solve_roster, solve_roster_weighted
from shiftopt.solvers.base import SolveParams

EMPLOYEE_COUNTS = (8, 12)
SEED = 0
TIME_LIMIT = 60.0
SHORTFALL_WEIGHTS = (1, 1_000, 100_000, 10_000_000)
FAIRNESS_WEIGHT = 1
PARAMS = SolveParams(
    time_limit_seconds=TIME_LIMIT, relative_gap_limit=0.0, num_workers=1, random_seed=SEED
)


def main() -> None:
    """Compare one weighted objective, min w * shortfall + cost + F, against the lexicographic
    order (shortfall first, then cost, then night spread). A small w trades coverage for cost, so
    understaffed hours rise while labour cost falls. Labour cost comes from the KPI of the roster,
    so every row is checked the same way. status is OPTIMAL only when that solve is proven."""
    writer = csv.writer(sys.stdout)
    writer.writerow(
        ("employees", "method", "shortfall_weight", "status", "understaffed", "labor_cost", "F")
    )
    for employee_count in EMPLOYEE_COUNTS:
        instance = weekly_instance(employee_count, SEED)
        lexicographic = solve_roster(instance, PARAMS)
        writer.writerow(_row(instance, employee_count, "lexicographic", None, lexicographic))
        for weight in SHORTFALL_WEIGHTS:
            outcome = solve_roster_weighted(
                instance,
                PARAMS,
                shortfall_weight=weight,
                fairness_weight=FAIRNESS_WEIGHT,
            )
            writer.writerow(_row(instance, employee_count, "weighted", weight, outcome))


def _row(
    instance: Instance,
    employee_count: int,
    method: str,
    weight: int | None,
    outcome: RosterOutcome,
) -> tuple[object, ...]:
    measures = compute_kpi(instance, outcome.solution)
    return (
        employee_count,
        method,
        "" if weight is None else weight,
        outcome.result.status,
        outcome.understaffed_hours,
        measures.labor_cost,
        outcome.night_spread,
    )


if __name__ == "__main__":
    main()
