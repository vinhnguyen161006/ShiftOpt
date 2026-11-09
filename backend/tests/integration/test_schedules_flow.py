import asyncio
from typing import Any

import pytest
from httpx import AsyncClient

from src.main import recover_interrupted_jobs
from src.schedules.models import RunStatus, SolveRun
from tests.integration.helpers import poll, solve_body

pytestmark = pytest.mark.integration


async def test_create_schedule_then_poll_until_finished(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    assert accepted.status_code == 202
    run = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")

    assert run["status"] == "succeeded", run["error"]
    assert run["hard_violations"] == 0
    assert run["solver_version"]
    assert run["params"]["random_seed"] == 0

    compliance = await client.get(f"/api/schedules/{run['id']}/compliance")
    assert compliance.json()["violations"] == []
    kpi = await client.get(f"/api/schedules/{run['id']}/kpi")
    assert kpi.json()["coverage_ratio"] >= 0.98


async def test_same_instance_and_seed_give_same_objective(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    objectives = []
    for _ in range(2):
        accepted = await client.post("/api/schedules", json=solve_body(seeded))
        run = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
        objectives.append(run["objective"])
    assert objectives[0] == objectives[1]


async def test_health_answers_while_a_solve_runs(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    solving = asyncio.create_task(client.post("/api/schedules", json=solve_body(seeded)))
    await asyncio.sleep(0.2)
    health = await asyncio.wait_for(client.get("/health"), timeout=2)
    assert health.status_code == 200
    await solving


async def test_stale_running_runs_are_failed_on_restart(
    app: Any, client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    run_id = accepted.json()["job_id"]
    async with app.state.session_factory() as session:
        run = await session.get(SolveRun, run_id)
        assert run is not None
        run.status = RunStatus.RUNNING
        await session.commit()

    await recover_interrupted_jobs(app.state.session_factory)

    recovered = (await client.get(f"/api/schedules/{run_id}")).json()
    assert recovered["status"] == "failed"
    assert recovered["error"] == "server restarted"


async def test_manual_edit_creates_new_run_and_keeps_original(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")

    edit = await client.post(
        f"/api/schedules/{original['id']}/edits",
        json={
            "assignments": [
                {"employee_code": "E1", "day": 0, "shift_name": "evening", "break_offset": 3},
                {"employee_code": "E1", "day": 1, "shift_name": "morning", "break_offset": 3},
            ]
        },
    )
    assert edit.status_code == 201
    edited = edit.json()
    assert edited["parent_run_id"] == original["id"]
    assert edited["status"] == "failed"
    assert edited["hard_violations"] >= 1

    compliance = await client.get(f"/api/schedules/{edited['id']}/compliance")
    kinds = {item["kind"] for item in compliance.json()["violations"]}
    assert "rest_between_shifts" in kinds

    untouched = await client.get(f"/api/schedules/{original['id']}/compliance")
    assert untouched.json()["violations"] == []


async def test_csv_exports_have_headers(client: AsyncClient, seeded: dict[str, Any]) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    run = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")

    assignments = await client.get(f"/api/schedules/{run['id']}/assignments.csv")
    coverage = await client.get(f"/api/schedules/{run['id']}/coverage.csv")

    assert assignments.headers["content-type"].startswith("text/csv")
    assert assignments.text.splitlines()[0].startswith("employee_code,day,shift_name")
    assert len(coverage.text.splitlines()) == 169


async def test_limits_reject_oversized_requests(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    too_many_workers = {**solve_body(seeded), "num_workers": 999}
    too_long = {**solve_body(seeded), "time_limit_seconds": 999999}
    assert (await client.post("/api/schedules", json=too_many_workers)).status_code == 422
    assert (await client.post("/api/schedules", json=too_long)).status_code == 422


async def test_repair_keeps_locked_days_and_counts_changes(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    assert original["status"] == "succeeded", original["error"]

    repair = await client.post(
        f"/api/schedules/{original['id']}/repair",
        json={
            "from_day": 2,
            "absences": [{"employee_code": "E1", "days": [3]}],
            "time_limit_seconds": 20.0,
            "num_workers": 1,
            "random_seed": 0,
        },
    )
    assert repair.status_code == 202
    repaired = await poll(client, f"/api/schedules/{repair.json()['job_id']}")

    assert repaired["status"] == "succeeded", repaired["error"]
    assert repaired["parent_run_id"] == original["id"]
    assert repaired["repair_from_day"] == 2
    assert repaired["hard_violations"] == 0
    assert repaired["changes"] is not None
    locked_before = [row for row in original["assignments"] if row["day"] < 2]
    locked_after = [row for row in repaired["assignments"] if row["day"] < 2]
    assert sorted(map(str, locked_after)) == sorted(map(str, locked_before))


async def test_repair_rejects_absence_on_locked_day(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")

    response = await client.post(
        f"/api/schedules/{original['id']}/repair",
        json={"from_day": 2, "absences": [{"employee_code": "E1", "days": [0]}]},
    )

    assert response.status_code == 422
    assert "locked day" in response.text


async def test_replacements_exclude_the_absent_employee(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    run = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    shift = run["assignments"][0]

    response = await client.get(
        f"/api/schedules/{run['id']}/replacements",
        params={"employee_code": shift["employee_code"], "day": shift["day"], "limit": 3},
    )

    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) <= 3
    assert all(item["employee_code"] != shift["employee_code"] for item in candidates)
    assert all(item["shift_name"] == shift["shift_name"] for item in candidates)


def _keys(rows: list[dict[str, Any]]) -> set[tuple[str, int, str]]:
    return {(row["employee_code"], row["day"], row["shift_name"]) for row in rows}


async def test_reroster_after_absence_keeps_earlier_days(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    assert original["status"] == "succeeded", original["error"]
    absent = next(a["employee_code"] for a in original["assignments"] if a["day"] == 3)

    reroster = await client.post(
        f"/api/schedules/{original['id']}/reroster",
        json={"employee_code": absent, "absent_days": [3]},
    )
    assert reroster.status_code == 202
    child = await poll(client, f"/api/schedules/{reroster.json()['job_id']}")

    assert child["status"] == "succeeded", child["error"]
    assert child["parent_run_id"] == original["id"]
    assert child["repair_from_day"] == 3
    assert not any(a["employee_code"] == absent and a["day"] == 3 for a in child["assignments"])
    before_absence = [a for a in original["assignments"] if a["day"] < 3]
    assert _keys(before_absence) <= _keys(child["assignments"])

    changes = (await client.get(f"/api/schedules/{child['id']}/changes")).json()
    assert any(r["employee_code"] == absent and r["day"] == 3 for r in changes["removed"])
    assert len(changes["added"]) == len(changes["removed"])


async def test_reroster_rejects_invalid_requests(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    absent = original["assignments"][0]["employee_code"]
    url = f"/api/schedules/{original['id']}/reroster"

    late_start = {"employee_code": absent, "absent_days": [3], "from_day": 4}
    assert (await client.post(url, json=late_start)).status_code == 422
    unknown = {"employee_code": "NOBODY", "absent_days": [3]}
    assert (await client.post(url, json=unknown)).status_code == 422
    repeated = {"employee_code": absent, "absent_days": [3, 3]}
    assert (await client.post(url, json=repeated)).status_code == 422
    assert (await client.get(f"/api/schedules/{original['id']}/changes")).status_code == 404


async def test_reroster_refuses_a_run_that_violates_the_law(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post("/api/schedules", json=solve_body(seeded))
    original = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    edit = await client.post(
        f"/api/schedules/{original['id']}/edits",
        json={
            "assignments": [
                {"employee_code": "E1", "day": 0, "shift_name": "evening", "break_offset": 3},
                {"employee_code": "E1", "day": 1, "shift_name": "morning", "break_offset": 3},
            ]
        },
    )
    refused = await client.post(
        f"/api/schedules/{edit.json()['id']}/reroster",
        json={"employee_code": "E1", "absent_days": [5]},
    )
    assert refused.status_code == 409


async def test_preview_warnings_answers_without_creating_a_run(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    before = await client.get("/api/schedules")
    response = await client.post("/api/schedules/preview-warnings", json=solve_body(seeded))

    assert response.status_code == 200
    assert isinstance(response.json()["warnings"], list)
    assert (await client.get("/api/schedules")).json() == before.json()


async def test_tight_budget_leaves_hours_short_but_run_still_succeeds(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    body = {**solve_body(seeded), "weekly_budget": 1}
    accepted = await client.post("/api/schedules", json=body)
    assert accepted.status_code == 202
    run = await poll(client, f"/api/schedules/{accepted.json()['job_id']}")

    assert run["status"] == "succeeded", run["error"]
    assert run["weekly_budget"] == 1
    assert run["understaffed_hours"] > 0
    assert run["hard_violations"] == 0
