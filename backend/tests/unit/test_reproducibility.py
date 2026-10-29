from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules

from src.employees.models import EmployeeRecord
from src.schedules.models import SolveRun
from src.schedules.schemas import SolveRequest
from src.schedules.service import solve_params
from src.schedules.snapshot import Snapshot, build_snapshot
from src.schedules.worker import solve_snapshot
from src.shifts.models import ShiftTemplate

PARAMS: dict[str, float] = {
    "time_limit_seconds": 60.0,
    "relative_gap_limit": 0.0,
    "num_workers": 1,
    "random_seed": 0,
}
PRINCIPLE_10_COLUMNS = {
    "instance_snapshot",
    "params",
    "solver",
    "solver_version",
    "solve_status",
    "objective",
    "best_bound",
    "gap",
    "wall_time_seconds",
    "solver_log",
}


def _snapshot() -> Snapshot:
    templates = [
        ShiftTemplate(name="night", start_hour=0, length_hours=8),
        ShiftTemplate(name="day", start_hour=8, length_hours=8),
        ShiftTemplate(name="evening", start_hour=16, length_hours=8),
    ]
    employees = [
        EmployeeRecord(
            code=f"E{index}",
            name=f"E{index}",
            hourly_wage=100,
            unavailable_days=[],
            preferred_days_off=[],
        )
        for index in range(2)
    ]
    demand = [0] * 168
    for hour in range(8, 16):
        demand[hour] = 1
    return build_snapshot(demand, templates, employees, LaborRules())


def _sorted_assignments(rows: list[dict[str, Any]]) -> list[tuple[str, int, str]]:
    return sorted((row["employee_code"], row["day"], row["shift_name"]) for row in rows)


def test_same_snapshot_and_seed_reproduce_objective_and_assignments() -> None:
    snapshot = _snapshot()

    first = solve_snapshot(snapshot, PARAMS)
    second = solve_snapshot(snapshot, PARAMS)

    assert first["solve_status"] == second["solve_status"]
    assert first["objective"] == second["objective"]
    assert _sorted_assignments(first["assignments"]) == _sorted_assignments(second["assignments"])


def test_solve_params_carry_seed_and_workers() -> None:
    payload = SolveRequest(
        demand_profile_id=1,
        shift_template_ids=[1],
        time_limit_seconds=30.0,
        num_workers=1,
        random_seed=7,
    )

    assert solve_params(payload) == {
        "time_limit_seconds": 30.0,
        "relative_gap_limit": 0.01,
        "num_workers": 1,
        "random_seed": 7,
    }


def test_solve_run_has_every_reproducibility_column() -> None:
    columns = {column.name for column in SolveRun.__table__.columns}

    assert PRINCIPLE_10_COLUMNS <= columns
