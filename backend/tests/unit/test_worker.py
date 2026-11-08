import os
from dataclasses import asdict
from typing import Any

import pytest
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.validation import validate

from src.analysis.worker import parallel_points, run_analysis, solve_sweep_point
from src.schedules.snapshot import instance_from_snapshot, solution_from_rows
from src.schedules.worker import solve_snapshot, to_solve_params

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


def test_demand_sweep_returns_hourly_staffing_and_scaled_demand() -> None:
    result = run_analysis(
        "demand_sweep",
        {"snapshot": _snapshot(), "params": PARAMS, "multipliers": [1.0, 2.0]},
    )

    for point, scale in zip(result["points"], (1, 2), strict=True):
        assert len(point["staff_by_hour"]) == 168
        assert point["required_by_hour"] == [value * scale for value in _day_zero_demand()]
        assert sum(point["staff_by_hour"]) > 0


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


def test_staffing_sweep_rederives_demand_for_each_value() -> None:
    load = [0.0] * 168
    load[8:16] = [3.0] * 8
    result = run_analysis(
        "staffing_sweep",
        {
            "snapshot": _snapshot(),
            "params": PARAMS,
            "assumption": "alpha",
            "values": [1.0, 2.0],
            "load": load,
            "night_from_sales": False,
            "base": {"alpha": 1.0, "productivity": 1.0, "min_staff": 1, "night_min_staff": 1},
        },
    )

    assert result["assumption"] == "alpha"
    assert [point["value"] for point in result["points"]] == [1.0, 2.0]
    assert result["points"][1]["understaffed_hours"] >= result["points"][0]["understaffed_hours"]


def test_unknown_analysis_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown analysis kind"):
        run_analysis("bogus", {"snapshot": _snapshot(), "params": PARAMS})


@pytest.mark.parametrize(
    ("cpus", "points", "workers", "expected"),
    [(16, 6, 1, 6), (16, 6, 8, 2), (16, 20, 1, 16), (4, 6, 8, 1), (None, 6, 1, 1), (16, 1, 1, 1)],
)
def test_parallel_points_respects_cpus_and_point_count(
    monkeypatch: pytest.MonkeyPatch,
    cpus: int | None,
    points: int,
    workers: int,
    expected: int,
) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: cpus)

    assert parallel_points(points, workers) == expected


def test_parallel_sweep_matches_solving_each_point_alone() -> None:
    multipliers = [1.0, 2.0]

    parallel = run_analysis(
        "demand_sweep",
        {"snapshot": _snapshot(), "params": PARAMS, "multipliers": multipliers},
    )

    instance = instance_from_snapshot(_snapshot())
    alone = [
        solve_sweep_point(instance, multiplier, to_solve_params(PARAMS))
        for multiplier in multipliers
    ]
    assert parallel["points"] == alone
