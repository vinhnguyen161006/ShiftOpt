from dataclasses import asdict
from typing import Any

import pytest
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.validation import validate

from src.analysis.worker import run_analysis
from src.schedules.snapshot import instance_from_snapshot, solution_from_rows
from src.schedules.worker import solve_snapshot

PARAMS: dict[str, float] = {
    "time_limit_seconds": 10.0,
    "relative_gap_limit": 0.0,
    "num_workers": 1,
    "random_seed": 0,
}


def _day_zero_demand() -> list[int]:
    demand = [0] * 168
    demand[8:16] = [1] * 8
    return demand


def _snapshot() -> dict[str, Any]:
    return {
        "demand": _day_zero_demand(),
        "shift_types": [{"name": "day", "start_hour": 8, "length": 8}],
        "employees": [
            {
                "id": code,
                "hourly_wage": 100,
                "unavailable_days": [],
                "preferred_days_off": [],
            }
            for code in ("E1", "E2")
        ],
        "rules": asdict(LaborRules()),
    }


def test_solve_snapshot_returns_validated_optimum() -> None:
    snapshot = _snapshot()

    payload = solve_snapshot(snapshot, PARAMS)

    assert payload["solve_status"] == "optimal"
    assert payload["objective"] is not None
    assert payload["understaffed_hours"] == 0
    solution = solution_from_rows(payload["assignments"])
    assert validate(instance_from_snapshot(snapshot), solution) == []


def test_solve_snapshot_is_reproducible() -> None:
    first = solve_snapshot(_snapshot(), PARAMS)
    second = solve_snapshot(_snapshot(), PARAMS)

    assert first["objective"] == second["objective"]


def test_demand_sweep_marks_each_point() -> None:
    result = run_analysis(
        "demand_sweep",
        {"snapshot": _snapshot(), "params": PARAMS, "multipliers": [1.0, 2.0]},
    )

    assert [point["multiplier"] for point in result["points"]] == [1.0, 2.0]
    assert all(point["proven"] for point in result["points"])


def test_marginal_cost_is_labeled_approximate_for_duals() -> None:
    result = run_analysis(
        "marginal_cost",
        {"snapshot": _snapshot(), "params": PARAMS, "hourly_wage": 100},
    )

    assert len(result["marginal_cost_by_hour"]) == 168
    assert len(result["lp_dual_by_hour"]) == 168
    assert result["approximate"] is True
    assert "approximation" in result["label"]


def test_lp_duals_return_one_value_per_hour() -> None:
    result = run_analysis(
        "lp_duals",
        {"snapshot": _snapshot(), "params": PARAMS, "hourly_wage": 100},
    )

    assert len(result["duals_by_hour"]) == 168
    assert result["approximate"] is True


def test_unknown_analysis_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown analysis kind"):
        run_analysis("bogus", {"snapshot": _snapshot(), "params": PARAMS})
