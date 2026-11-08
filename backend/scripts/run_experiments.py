import argparse
import csv
import math
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from shiftopt import kpi
from shiftopt.baseline import greedy_roster
from shiftopt.domain import Employee, Instance, RepairSpec, Solution
from shiftopt.experiments import (
    Scenario,
    demand_scenarios,
    shift_pattern_scenarios,
    staffing_scenarios,
)
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.schedule_diff import diff_solutions
from shiftopt.solvers.base import SolveParams
from shiftopt.validation import validate

from scripts.baseline_store18 import baseline_instance

ROOT = Path(__file__).resolve().parents[2]
RANKING = ROOT / "docs" / "experiments" / "store_ranking.csv"
DEFAULT_OUT = ROOT / "docs" / "experiments" / "scenario_results.csv"
DEFAULT_STORES = (18,)
PRODUCTIVITY_VARIANTS = (3.0, 5.0)
ABSENCE_DAYS = (1, 2, 3)
ABSENCE_FROM_DAY = 2
HOURS_PER_EMPLOYEE = 40
EMPLOYEE_SLACK = 1.25
MIN_EMPLOYEES = 8
COLUMNS = (
    "store",
    "scenario",
    "method",
    "seed",
    "employees",
    "status",
    "tiers",
    "shortfall",
    "labor_cost",
    "understaffed",
    "overstaffed",
    "coverage",
    "violations",
    "changes",
    "wall_s",
)


@dataclass(frozen=True)
class Plan:
    time_limit: float
    seeds: tuple[int, ...]
    quick: bool


def employee_count(demand_hours: int) -> int:
    return max(MIN_EMPLOYEES, math.ceil(EMPLOYEE_SLACK * demand_hours / HOURS_PER_EMPLOYEE))


def store_base(store: int, productivity: float = 4.0) -> Instance:
    probe = baseline_instance(store, MIN_EMPLOYEES, productivity)
    count = employee_count(sum(probe.demand))
    return baseline_instance(store, count, productivity)


def with_employees(instance: Instance, count: int) -> Instance:
    staff = tuple(Employee(f"e{index:02d}", 100) for index in range(count))
    return replace(instance, employees=staff)


def _row(
    store: int,
    scenario: str,
    method: str,
    seed: int,
    instance: Instance,
    solution: Solution | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "store": store,
        "scenario": scenario,
        "method": method,
        "seed": seed,
        "employees": len(instance.employees),
        "status": result.get("status", "error"),
        "tiers": result.get("tiers", ""),
        "shortfall": result.get("shortfall", ""),
        "labor_cost": "",
        "understaffed": "",
        "overstaffed": "",
        "coverage": "",
        "violations": "",
        "changes": result.get("changes", ""),
        "wall_s": result.get("wall_s", ""),
    }
    if solution is not None:
        measures = kpi.compute_kpi(instance, solution)
        row.update(
            labor_cost=kpi.labor_cost(instance, solution),
            understaffed=measures.understaffed_hours,
            overstaffed=measures.overstaffed_hours,
            coverage=round(measures.coverage_ratio, 4),
            violations=len(validate(instance, solution)),
        )
    return row


def _solve_cpsat(
    instance: Instance, seed: int, plan: Plan
) -> tuple[Solution | None, dict[str, Any]]:
    params = SolveParams(
        time_limit_seconds=plan.time_limit,
        relative_gap_limit=0.01,
        num_workers=1,
        random_seed=seed,
    )
    started = time.perf_counter()
    outcome = solve_roster(instance, params)
    wall = time.perf_counter() - started
    result = outcome.result
    solved = outcome.understaffed_hours is not None
    info = {
        "status": result.status.value,
        "tiers": "/".join(phase.status.value for phase in outcome.phases),
        "shortfall": outcome.phases[0].objective if outcome.phases else "",
        "wall_s": round(wall, 2),
        "changes": outcome.changes if outcome.changes is not None else "",
    }
    return (outcome.solution if solved else None), info


def _solve_greedy(instance: Instance) -> tuple[Solution, dict[str, Any]]:
    started = time.perf_counter()
    solution = greedy_roster(instance)
    wall = time.perf_counter() - started
    return solution, {"status": "feasible", "wall_s": round(wall, 2)}


def _scenario_rows(store: int, scenario: Scenario, plan: Plan) -> list[dict[str, Any]]:
    rows = []
    seeds = plan.seeds if scenario.name == "base" else plan.seeds[:1]
    for seed in seeds:
        solution, info = _solve_cpsat(scenario.instance, seed, plan)
        rows.append(_row(store, scenario.name, "cpsat", seed, scenario.instance, solution, info))
    solution, info = _solve_greedy(scenario.instance)
    rows.append(_row(store, scenario.name, "greedy", 0, scenario.instance, solution, info))
    return rows


def _absent_employee(solution: Solution) -> str:
    counts: dict[str, int] = {}
    for assignment in solution.assignments:
        counts[assignment.employee_id] = counts.get(assignment.employee_id, 0) + 1
    return min(counts, key=lambda code: (-counts[code], code))


def _absence_rows(store: int, base: Instance, plan: Plan) -> list[dict[str, Any]]:

    rows: list[dict[str, Any]] = []
    cpsat_base = solve_roster(base, SolveParams(time_limit_seconds=plan.time_limit, num_workers=1))
    if cpsat_base.understaffed_hours is None:
        return rows
    greedy_base = greedy_roster(base)
    absent = _absent_employee(cpsat_base.solution)
    for count in ABSENCE_DAYS:
        days = tuple(range(ABSENCE_FROM_DAY, ABSENCE_FROM_DAY + count))
        name = f"absence-{count}d"
        staff = tuple(
            replace(e, unavailable_days=e.unavailable_days | frozenset(days))
            if e.id == absent
            else e
            for e in base.employees
        )
        changed = replace(base, employees=staff)
        repair = RepairSpec(baseline=cpsat_base.solution, from_day=ABSENCE_FROM_DAY)
        started = time.perf_counter()
        outcome = solve_roster(
            changed,
            SolveParams(time_limit_seconds=plan.time_limit, num_workers=1, random_seed=0),
            repair=repair,
        )
        wall = time.perf_counter() - started
        cpsat_solution = outcome.solution if outcome.understaffed_hours is not None else None
        cpsat_info = {
            "status": outcome.result.status.value,
            "tiers": "/".join(phase.status.value for phase in outcome.phases),
            "shortfall": outcome.phases[0].objective if outcome.phases else "",
            "changes": outcome.changes if outcome.changes is not None else "",
            "wall_s": round(wall, 2),
        }
        rows.append(_row(store, name, "cpsat", 0, changed, cpsat_solution, cpsat_info))
        greedy_after = greedy_roster(changed)
        greedy_changes = len(diff_solutions(greedy_base, greedy_after).added) + len(
            diff_solutions(greedy_base, greedy_after).removed
        )
        rows.append(
            _row(
                store,
                name,
                "greedy",
                0,
                changed,
                greedy_after,
                {"status": "feasible", "changes": greedy_changes},
            )
        )
    return rows


def scenarios_for(store: int, base: Instance, quick: bool) -> list[Scenario]:
    scenarios = demand_scenarios(base)
    scenarios += staffing_scenarios(base)
    scenarios += shift_pattern_scenarios(base)
    for productivity in PRODUCTIVITY_VARIANTS:
        variant = store_base(store, productivity)
        scenarios.append(
            Scenario(f"p={productivity:g}", with_employees(variant, len(base.employees)))
        )
    if quick:
        keep = {"base", "lambda=1.1", "minus-1"}
        scenarios = [s for s in scenarios if s.name in keep]
    return scenarios


def run_store(store: int, plan: Plan) -> list[dict[str, Any]]:
    base = store_base(store)
    rows: list[dict[str, Any]] = []
    for scenario in scenarios_for(store, base, plan.quick):
        rows.extend(_scenario_rows(store, scenario, plan))
    if not plan.quick:
        rows.extend(_absence_rows(store, base, plan))
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def selected_stores() -> tuple[int, ...]:
    if not RANKING.exists():
        return DEFAULT_STORES
    with RANKING.open(encoding="utf-8") as handle:
        stores = tuple(
            int(row["store"]) for row in csv.DictReader(handle) if row["selected"] == "yes"
        )
    return stores or DEFAULT_STORES


def summary(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    header = (
        "| store | scenario | CP-SAT cost | greedy cost | greedy vs CP-SAT "
        "| CP-SAT under | greedy under | CP-SAT tiers | changes (CP-SAT / greedy) |"
    )
    lines = [header, "|---|---|---|---|---|---|---|---|---|"]
    keys = []
    for row in rows:
        key = (row["store"], row["scenario"])
        if key not in keys:
            keys.append(key)
    for store, scenario in keys:
        cp = [
            r
            for r in rows
            if r["store"] == store and r["scenario"] == scenario and r["method"] == "cpsat"
        ]
        gr = [
            r
            for r in rows
            if r["store"] == store and r["scenario"] == scenario and r["method"] == "greedy"
        ]
        if not cp or not gr:
            continue
        c, g = cp[0], gr[0]
        delta = "-"
        comparable = c["understaffed"] == g["understaffed"] and c["labor_cost"] and g["labor_cost"]
        if comparable:
            delta = f"{(float(g['labor_cost']) / float(c['labor_cost']) - 1) * 100:+.1f}%"
        changes = f"{c['changes'] or '-'} / {g['changes'] or '-'}"
        lines.append(
            f"| {store} | {scenario} | {c['labor_cost'] or '-'} | {g['labor_cost'] or '-'} "
            f"| {delta} | {c['understaffed'] or '-'} | {g['understaffed'] or '-'} "
            f"| {c['tiers']} | {changes} |"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="CP-SAT versus greedy baseline experiments")
    parser.add_argument("--stores", type=int, nargs="+")
    parser.add_argument("--time-limit", type=float, default=30.0)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    if args.summary:
        print(summary(args.out))
        return 0
    stores = tuple(args.stores) if args.stores else selected_stores()
    plan = Plan(time_limit=args.time_limit, seeds=tuple(args.seeds), quick=args.quick)
    estimate = len(stores) * (1 if args.quick else 24) * args.time_limit / 60
    print(
        f"stores={stores} time_limit={args.time_limit}s; upper bound about {estimate:.0f} min",
        file=sys.stderr,
    )
    rows: list[dict[str, Any]] = []
    for store in stores:
        try:
            rows.extend(run_store(store, plan))
        except Exception as error:
            rows.append(
                {"store": store, "scenario": "store", "method": "error", "status": str(error)}
            )
    write_csv(rows, args.out)
    print(f"wrote {len(rows)} rows to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
