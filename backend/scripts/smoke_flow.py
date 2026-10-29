import argparse
import sys
import time
import uuid
from typing import Any

import httpx

TERMINAL = ("succeeded", "failed")
DAY_DEMAND = [2 if 8 <= hour < 16 else 0 for hour in range(168)]
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


def check_sweep(client: httpx.Client, profile_id: int, shift_ids: list[int]) -> None:
    accepted = client.post(
        "/api/analysis/demand-sweep",
        json={"solve": solve_body(profile_id, shift_ids, 20), "multipliers": [0.9, 1.0]},
    )
    expect(accepted.status_code == 202, f"demand-sweep: {accepted.status_code} {accepted.text}")
    sweep = poll(client, f"/api/analysis/{accepted.json()['job_id']}")
    expect(sweep["status"] == "succeeded", f"sweep failed: {sweep['error']}")


def run_flow(base_url: str) -> None:
    tag = uuid.uuid4().hex[:6]
    with httpx.Client(base_url=base_url, timeout=60) as client:
        profile_id, shift_ids = seed(client, tag)
        run = check_optimize(client, profile_id, shift_ids)
        check_manual_edit(client, run, tag)
        check_sweep(client, profile_id, shift_ids)


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
