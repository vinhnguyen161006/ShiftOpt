"""Load the demo data set through the public API: 30 employees and three 8-hour shift templates.
Demand comes from the sales ingest on the demand page. Each collection is seeded only when it
is empty, so running it again never duplicates rows and never touches data entered by users."""

import argparse
import http.cookiejar
import json
import os
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
READY_ATTEMPTS = 60
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(base_url: str, method: str, path: str, body: object = None) -> Any:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base_url}{path}", data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with OPENER.open(req, timeout=60) as response:
        return json.loads(response.read() or b"null")


def wait_until_ready(base_url: str) -> None:
    health_url = base_url.removesuffix("/api") + "/health"
    for _ in range(READY_ATTEMPTS):
        try:
            with urllib.request.urlopen(health_url, timeout=5):
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


def sign_in(base_url: str, email: str, password: str) -> None:
    credentials = {"email": email, "password": password}
    try:
        request(base_url, "POST", "/auth/register", {**credentials, "display_name": "Demo"})
    except urllib.error.HTTPError as error:
        if error.code != 409:
            raise SystemExit(f"sign-up failed with status {error.code}") from error
        request(base_url, "POST", "/auth/login", credentials)


def demo_credentials() -> tuple[str, str]:
    email = os.environ.get("SHIFTOPT_DEMO_EMAIL", "")
    password = os.environ.get("SHIFTOPT_DEMO_PASSWORD", "")
    if not email or not password:
        raise SystemExit("set SHIFTOPT_DEMO_EMAIL and SHIFTOPT_DEMO_PASSWORD")
    return email, password


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the ShiftOpt demo data when empty.")
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    base_url: str = parser.parse_args().base_url.rstrip("/")
    wait_until_ready(base_url)
    sign_in(base_url, *demo_credentials())
    seed_employees(base_url)
    seed_shift_templates(base_url)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
