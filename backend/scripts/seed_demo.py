"""Load the demo data set through the public API: 30 employees, three 8-hour shift templates and
the FreshRetailNet store 18 demand profile. Each collection is seeded only when it is empty, so
running it again never duplicates rows and never touches data entered by users."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

EMPLOYEE_COUNT = 30
HOURLY_WAGE = 100
PART_TIME_CODE = "E07"
PART_TIME_WEEKLY_HOURS = 24
SHIFT_TEMPLATES = (("\u0110\xeam", 0), ("Ng\xe0y", 8), ("T\u1ed1i", 16))
SHIFT_LENGTH_HOURS = 8
STORE_ID = 18
PROFILE_NAME = "Store 18 demo"
STORE_CONVERSION = {"alpha": 1.0, "productivity": 4.0, "min_staff": 1, "night_min_staff": 1}
READY_ATTEMPTS = 60


def request(base_url: str, method: str, path: str, body: object = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base_url}{path}", data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read() or b"null")


def wait_until_ready(base_url: str) -> None:
    for _ in range(READY_ATTEMPTS):
        try:
            request(base_url, "GET", "/employees")
            return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(2)
    raise SystemExit(f"API at {base_url} did not answer")


def employee_body(index: int) -> dict[str, Any]:
    code = f"E{index:02d}"
    body: dict[str, Any] = {"code": code, "name": f"Employee {index}", "hourly_wage": HOURLY_WAGE}
    if code == PART_TIME_CODE:
        body["max_weekly_hours"] = PART_TIME_WEEKLY_HOURS
    return body


def seed_employees(base_url: str) -> None:
    if request(base_url, "GET", "/employees"):
        print("employees: already present, skipped")
        return
    for index in range(1, EMPLOYEE_COUNT + 1):
        request(base_url, "POST", "/employees", employee_body(index))
    print(f"employees: created {EMPLOYEE_COUNT}")


def seed_shift_templates(base_url: str) -> None:
    if request(base_url, "GET", "/shift-templates"):
        print("shift templates: already present, skipped")
        return
    for name, start_hour in SHIFT_TEMPLATES:
        body = {"name": name, "start_hour": start_hour, "length_hours": SHIFT_LENGTH_HOURS}
        request(base_url, "POST", "/shift-templates", body)
    print(f"shift templates: created {len(SHIFT_TEMPLATES)}")


def seed_demand_profile(base_url: str) -> None:
    if request(base_url, "GET", "/demand-profiles"):
        print("demand profiles: already present, skipped")
        return
    body = {"name": PROFILE_NAME, "store_id": STORE_ID, "conversion_params": STORE_CONVERSION}
    try:
        request(base_url, "POST", "/demand-profiles/from-dataset", body)
    except urllib.error.HTTPError as error:
        print(f"demand profiles: not created ({error.code} {error.read().decode()})")
        return
    print(f"demand profiles: created '{PROFILE_NAME}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the ShiftOpt demo data when empty.")
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    base_url: str = parser.parse_args().base_url.rstrip("/")
    wait_until_ready(base_url)
    seed_employees(base_url)
    seed_shift_templates(base_url)
    seed_demand_profile(base_url)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
