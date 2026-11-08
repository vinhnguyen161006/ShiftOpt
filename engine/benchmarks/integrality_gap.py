import csv
import sys

from benchmarks.compare_solvers import INSTANCES, WAGE
from benchmarks.run_roster_scale import weekly_instance
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.models.roster_mip import solve_roster_mip
from shiftopt.solvers.base import SolveParams

ROSTER_EMPLOYEES = 10
ROSTER_SEEDS = (0, 1, 2)
TIME_LIMIT = 60.0
PARAMS = SolveParams(
    time_limit_seconds=TIME_LIMIT, relative_gap_limit=0.0, num_workers=1, random_seed=0
)


def gap_percent(lp: float | None, ip: float | None) -> float | None:
    if lp is None or ip is None:
        return None
    return 100.0 * (ip - lp) / max(1.0, abs(ip))


def aggregate_rows() -> list[tuple[str, str, str, float | None, float | None, float | None, str]]:
    rows = []
    for name, build in INSTANCES:
        instance = build()
        lp = solve_with_implicit_breaks(instance, WAGE, PARAMS, relax=True)
        ip = solve_with_implicit_breaks(instance, WAGE, PARAMS, relax=False)
        rows.append(
            (
                "aggregate",
                name,
                "cost",
                lp.result.objective,
                ip.result.objective,
                gap_percent(lp.result.objective, ip.result.objective),
                str(ip.result.status),
            )
        )
    return rows


def roster_rows() -> list[tuple[str, str, str, float | None, float | None, float | None, str]]:
    rows = []
    for seed in ROSTER_SEEDS:
        instance = weekly_instance(ROSTER_EMPLOYEES, seed)
        lp = solve_roster_mip(instance, PARAMS, relax=True)
        ip = solve_roster_mip(instance, PARAMS)
        for tier_index, tier_name in enumerate(("shortfall", "cost")):
            lp_tier = lp.phases[tier_index].objective if len(lp.phases) > tier_index else None
            ip_tier = ip.phases[tier_index].objective if len(ip.phases) > tier_index else None
            status = str(ip.phases[tier_index].status) if len(ip.phases) > tier_index else "none"
            rows.append(
                (
                    "per_employee",
                    f"seed{seed}_{ROSTER_EMPLOYEES}emp",
                    tier_name,
                    lp_tier,
                    ip_tier,
                    gap_percent(lp_tier, ip_tier),
                    status,
                )
            )
    return rows


def main() -> None:
    """Integrality gap per model: the LP relaxation objective z_lp against the integer optimum
    z_ip, both from the same rows. gap_pct = 100 (z_ip - z_lp) / max(1, z_ip). The duals used in
    the sensitivity analysis come from the same relaxation, so this gap is the reason they are
    labelled approximate. A missing value means that solve produced no objective."""
    writer = csv.writer(sys.stdout)
    writer.writerow(("model", "instance", "tier", "z_lp", "z_ip", "gap_pct", "ip_status"))
    for row in aggregate_rows() + roster_rows():
        writer.writerow(row)


if __name__ == "__main__":
    main()
