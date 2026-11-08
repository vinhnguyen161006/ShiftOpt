from dataclasses import asdict
from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules

from src.analysis.worker import run_analysis

DEMAND = [1 if 8 <= hour % 24 < 16 else 0 for hour in range(168)]
SHIFTS = [
    {"name": "night", "start_hour": 0, "length": 8},
    {"name": "day", "start_hour": 8, "length": 8},
    {"name": "evening", "start_hour": 16, "length": 8},
]


def _employee(code: str) -> dict[str, Any]:
    return {
        "id": code,
        "hourly_wage": 100,
        "max_weekly_hours": None,
        "unavailable_days": [],
        "preferred_days_off": [],
    }


def test_baseline_compare_reports_cpsat_and_greedy_rows() -> None:
    snapshot = {
        "demand": DEMAND,
        "shift_types": SHIFTS,
        "employees": [_employee("e0"), _employee("e1")],
        "rules": asdict(LaborRules()),
    }
    params = {
        "time_limit_seconds": 5.0,
        "relative_gap_limit": 0.01,
        "num_workers": 1,
        "random_seed": 0,
    }
    result = run_analysis("baseline_compare", {"snapshot": snapshot, "params": params})

    cpsat, greedy = result["points"]
    assert cpsat["method"] == "cpsat"
    assert greedy["method"] == "greedy"
    assert greedy["solve_status"] == "feasible"
    assert greedy["proven"] is False
    assert greedy["labor_cost"] is not None
