import argparse
import sys
import time
import uuid
from typing import Any

import httpx

TERMINAL = ("succeeded", "failed")
DAY_DEMAND = [2 if 8 <= hour % 24 < 16 else 0 for hour in range(168)]
EMPLOYEE_COUNT = 25
SHIFT_TEMPLATES = (("day", 8), ("early", 6), ("evening", 14))
REST_KIND = "rest_between_shifts"


class SmokeError(RuntimeError):
    pass


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def poll(client: httpx.Client, url: str, attempts: int = 300) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for _ in range(attempts):
        body = client.get(url).json()
        if body["status"] in TERMINAL:
            return body
        time.sleep(1)
    raise SmokeError(f"job at {url} did not finish: {body}")


def seed(client: httpx.Client, tag: str) -> tuple[int, list[int]]:
    profile = client.post(
        "/api/demand-profiles", json={"name": f"smoke {tag}", "required_staff": DAY_DEMAND}
    )
    expect(profile.status_code == 201, f"demand profile: {profile.status_code} {profile.text}")
    shift_ids: list[int] = []
    for name, start in SHIFT_TEMPLATES:
        template = client.post(
            "/api/shift-templates",
            json={"name": f"{name}-{tag}", "start_hour": start, "length_hours": 8},
        )
        expect(template.status_code == 201, f"shift template: {template.text}")
        shift_ids.append(template.json()["id"])
    for index in range(EMPLOYEE_COUNT):
        employee = client.post(
            "/api/employees",
            json={"code": f"{tag}{index:02d}", "name": f"Smoke {index}", "hourly_wage": 100},
        )
        expect(employee.status_code == 201, f"employee: {employee.text}")
    return profile.json()["id"], shift_ids


def solve_body(profile_id: int, shift_ids: list[int], time_limit: float) -> dict[str, Any]:
    return {
        "demand_profile_id": profile_id,
        "shift_template_ids": shift_ids,
        "time_limit_seconds": time_limit,
        "relative_gap_limit": 0.01,
        "num_workers": 4,
        "random_seed": 0,
    }


def check_optimize(client: httpx.Client, profile_id: int, shift_ids: list[int]) -> dict[str, Any]:
    accepted = client.post("/api/schedules", json=solve_body(profile_id, shift_ids, 60))
    expect(accepted.status_code == 202, f"POST schedules: {accepted.status_code} {accepted.text}")
    run = poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    expect(run["status"] == "succeeded", f"solve failed: {run['error']}")
    expect(run["hard_violations"] == 0, f"hard violations: {run['hard_violations']}")
    run_id = run["id"]
    compliance = client.get(f"/api/schedules/{run_id}/compliance").json()
    expect(compliance["violations"] == [], f"compliance: {compliance['violations']}")
    kpi = client.get(f"/api/schedules/{run_id}/kpi").json()
    expect(kpi["coverage_ratio"] >= 0.98, f"coverage {kpi['coverage_ratio']}")
    csv_response = client.get(f"/api/schedules/{run_id}/assignments.csv")
    expect(csv_response.status_code == 200, f"assignments.csv: {csv_response.status_code}")
    expect(csv_response.text.startswith("employee_code,"), "assignments.csv header")
    return run


def check_manual_edit(client: httpx.Client, run: dict[str, Any], tag: str) -> None:
    victim = f"{tag}00"
    kept = [row for row in run["assignments"] if row["employee_code"] != victim]
    evening = {"employee_code": victim, "day": 0, "shift_name": f"evening-{tag}"}
    early = {"employee_code": victim, "day": 1, "shift_name": f"early-{tag}"}
    edited_rows = [*kept, {**evening, "break_offset": None}, {**early, "break_offset": None}]
    edit = client.post(f"/api/schedules/{run['id']}/edits", json={"assignments": edited_rows})
    expect(edit.status_code == 201, f"POST edits: {edit.status_code} {edit.text}")
    edited = edit.json()
    expect(edited["status"] == "failed", f"edited run status {edited['status']}")
    expect(edited["hard_violations"] > 0, "edited run reports no violations")
    kinds = {
        violation["kind"]
        for violation in client.get(f"/api/schedules/{edited['id']}/compliance").json()[
            "violations"
        ]
    }
    expect(REST_KIND in kinds, f"expected {REST_KIND}, got {sorted(kinds)}")
    original = client.get(f"/api/schedules/{run['id']}/compliance").json()
    expect(original["violations"] == [], "original schedule was changed by the edit")


def repair_body(time_limit: float = 20.0) -> dict[str, Any]:
    return {
        "time_limit_seconds": time_limit,
        "relative_gap_limit": 0.01,
        "num_workers": 4,
        "random_seed": 0,
    }


def first_on_day(run: dict[str, Any], day: int) -> dict[str, Any]:
    matches: list[dict[str, Any]] = [row for row in run["assignments"] if row["day"] == day]
    expect(bool(matches), f"no assignment on day {day} to test with")
    first: dict[str, Any] = matches[0]
    return first


def check_repair(client: httpx.Client, run: dict[str, Any]) -> dict[str, Any]:
    absent = first_on_day(run, 3)["employee_code"]
    body = {**repair_body(), "from_day": 2, "absences": [{"employee_code": absent, "days": [3]}]}
    accepted = client.post(f"/api/schedules/{run['id']}/repair", json=body)
    expect(accepted.status_code == 202, f"POST repair: {accepted.status_code} {accepted.text}")
    repaired = poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    expect(repaired["status"] == "succeeded", f"repair failed: {repaired['error']}")
    expect(
        repaired["hard_violations"] == 0, f"repair hard violations: {repaired['hard_violations']}"
    )
    expect(repaired["repair_from_day"] == 2, f"repair_from_day {repaired['repair_from_day']}")
    expect(repaired["changes"] is not None, "repair reports no change count")
    locked_before = sorted(str(row) for row in run["assignments"] if row["day"] < 2)
    locked_after = sorted(str(row) for row in repaired["assignments"] if row["day"] < 2)
    expect(locked_before == locked_after, "repair changed a locked day")
    expect(
        not any(
            row["employee_code"] == absent and row["day"] == 3 for row in repaired["assignments"]
        ),
        "absent employee still assigned on day 3",
    )
    changes = client.get(f"/api/schedules/{repaired['id']}/changes")
    expect(changes.status_code == 200, f"GET changes: {changes.status_code}")
    body_changes = changes.json()
    expect(len(body_changes["added"]) == len(body_changes["removed"]), "added and removed differ")
    return repaired


def check_repair_rejects_locked_absence(client: httpx.Client, run: dict[str, Any]) -> None:
    absent = first_on_day(run, 0)["employee_code"]
    body = {**repair_body(), "from_day": 2, "absences": [{"employee_code": absent, "days": [0]}]}
    refused = client.post(f"/api/schedules/{run['id']}/repair", json=body)
    expect(refused.status_code == 422, f"locked absence accepted: {refused.status_code}")


def check_replacements(client: httpx.Client, run: dict[str, Any]) -> dict[str, Any]:
    target = first_on_day(run, 1)
    response = client.get(
        f"/api/schedules/{run['id']}/replacements",
        params={"employee_code": target["employee_code"], "day": target["day"]},
    )
    expect(response.status_code == 200, f"replacements: {response.status_code} {response.text}")
    candidates = response.json()
    expect(bool(candidates), "no replacement candidate found")
    busy = {row["employee_code"] for row in run["assignments"] if row["day"] == target["day"]}
    expect(
        all(item["employee_code"] not in busy for item in candidates),
        "replacement candidate already works that day",
    )
    pick = candidates[0]
    rows = [row for row in run["assignments"] if row is not target]
    rows.append(
        {
            "employee_code": pick["employee_code"],
            "day": target["day"],
            "shift_name": pick["shift_name"],
            "break_offset": pick["break_offset"],
        }
    )
    applied = client.post(f"/api/schedules/{run['id']}/edits", json={"assignments": rows})
    expect(applied.status_code == 201, f"apply replacement: {applied.status_code} {applied.text}")
    result: dict[str, Any] = applied.json()
    expect(
        result["hard_violations"] == 0, f"replacement hard violations {result['hard_violations']}"
    )
    expect(result["status"] == "succeeded", f"replacement status {result['status']}")
    return result


def check_reroster(client: httpx.Client, run: dict[str, Any]) -> None:
    absent = first_on_day(run, 4)["employee_code"]
    accepted = client.post(
        f"/api/schedules/{run['id']}/reroster",
        json={"employee_code": absent, "absent_days": [4]},
    )
    expect(accepted.status_code == 202, f"POST reroster: {accepted.status_code} {accepted.text}")
    child = poll(client, f"/api/schedules/{accepted.json()['job_id']}")
    expect(child["status"] == "succeeded", f"reroster failed: {child['error']}")
    expect(child["hard_violations"] == 0, f"reroster hard violations {child['hard_violations']}")
    expect(child["repair_from_day"] == 4, f"reroster from_day {child['repair_from_day']}")
    expect(
        not any(row["employee_code"] == absent and row["day"] == 4 for row in child["assignments"]),
        "absent employee still assigned on the absence day",
    )


def check_sweep(client: httpx.Client, profile_id: int, shift_ids: list[int]) -> None:
    accepted = client.post(
        "/api/analysis/demand-sweep",
        json={
            "solve": solve_body(profile_id, shift_ids, 20),
            "multipliers": [0.8, 1.0, 1.3],
        },
    )
    expect(accepted.status_code == 202, f"demand-sweep: {accepted.status_code} {accepted.text}")
    sweep = poll(client, f"/api/analysis/{accepted.json()['job_id']}")
    expect(sweep["status"] == "succeeded", f"sweep failed: {sweep['error']}")
    points = sweep["result"]["points"]
    expect(len(points) == 3, f"sweep returned {len(points)} points")
    expect(all(point["solve_status"] for point in points), "sweep point without status")


def check_fairness_sweep(client: httpx.Client, profile_id: int, shift_ids: list[int]) -> None:
    accepted = client.post(
        "/api/analysis/fairness-sweep",
        json={"solve": solve_body(profile_id, shift_ids, 20), "tolerances": [0.0, 5.0]},
    )
    expect(accepted.status_code == 202, f"fairness-sweep: {accepted.status_code} {accepted.text}")
    sweep = poll(client, f"/api/analysis/{accepted.json()['job_id']}")
    expect(sweep["status"] == "succeeded", f"fairness sweep failed: {sweep['error']}")
    points = sweep["result"]["points"]
    expect(len(points) == 2, f"fairness sweep returned {len(points)} points")
    expect(points[0]["cost_increase_percent"] == 0.0, "tolerance 0 is not the cost baseline")


def run_flow(base_url: str) -> None:
    tag = uuid.uuid4().hex[:6]
    with httpx.Client(base_url=base_url, timeout=60) as client:
        profile_id, shift_ids = seed(client, tag)
        run = check_optimize(client, profile_id, shift_ids)
        check_manual_edit(client, run, tag)
        check_repair(client, run)
        check_repair_rejects_locked_absence(client, run)
        check_replacements(client, run)
        check_reroster(client, run)
        check_sweep(client, profile_id, shift_ids)
        check_fairness_sweep(client, profile_id, shift_ids)


def main(base_url: str) -> int:
    try:
        run_flow(base_url)
    except (SmokeError, httpx.HTTPError) as error:
        print(f"smoke flow failed: {error}", file=sys.stderr)
        return 1
    print("smoke flow passed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-end API smoke test")
    parser.add_argument("--base-url", default="http://localhost:3000")
    args = parser.parse_args()
    raise SystemExit(main(args.base_url))
