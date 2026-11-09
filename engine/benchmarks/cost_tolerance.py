import csv
import sys
from dataclasses import replace

from benchmarks.run_roster_scale import weekly_instance
from shiftopt.domain import Instance
from shiftopt.kpi import labor_cost
from shiftopt.models.roster_cpsat import RosterOutcome, solve_roster
from shiftopt.solvers.base import SolveParams

EMPLOYEE_COUNTS = (12, 20)
WAGES = (100, 120, 150)
SEED = 0
TIME_LIMIT = 60.0
TOLERANCES = (0.0, 1.0, 2.0, 5.0, 10.0)


def main() -> None:
    """Trade labour cost for fairness. Wages differ across employees so that the cheapest
    employees attract the night shifts at tolerance 0. Each row is a full solve at one tolerance,
    with the same time limit and seed. cost_increase_percent is measured against the tolerance 0
    roster, using kpi.labor_cost of the returned roster. status is OPTIMAL only when every tier of
    that solve is proven."""
    writer = csv.writer(sys.stdout)
    writer.writerow(
        (
            "employees",
            "tolerance_percent",
            "status",
            "labor_cost",
            "cost_increase_percent",
            "night_spread",
            "hours_spread",
            "understaffed",
        )
    )
    for employee_count in EMPLOYEE_COUNTS:
        instance = _with_wage_mix(weekly_instance(employee_count, SEED))
        base_cost: int | None = None
        for tolerance in TOLERANCES:
            params = SolveParams(
                time_limit_seconds=TIME_LIMIT,
                relative_gap_limit=0.0,
                num_workers=1,
                random_seed=SEED,
                cost_tolerance_percent=tolerance,
            )
            outcome = solve_roster(instance, params)
            cost = (
                labor_cost(instance, outcome.solution)
                if outcome.understaffed_hours is not None
                else None
            )
            if tolerance == 0.0:
                base_cost = cost
            writer.writerow(_row(employee_count, tolerance, outcome, cost, base_cost))


def _with_wage_mix(instance: Instance) -> Instance:
    employees = tuple(
        replace(employee, hourly_wage=WAGES[index % len(WAGES)])
        for index, employee in enumerate(instance.employees)
    )
    return replace(instance, employees=employees)


def _row(
    employee_count: int,
    tolerance: float,
    outcome: RosterOutcome,
    cost: int | None,
    base_cost: int | None,
) -> tuple[object, ...]:
    increase = (
        None
        if cost is None or base_cost is None or base_cost == 0
        else round(100 * (cost - base_cost) / base_cost, 2)
    )
    return (
        employee_count,
        tolerance,
        outcome.result.status.value,
        cost,
        increase,
        outcome.night_spread,
        outcome.hours_spread,
        outcome.understaffed_hours,
    )


if __name__ == "__main__":
    main()
