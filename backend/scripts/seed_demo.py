"""Create the demo account through the public API. Signing up gives every account its starter
data (30 employees and three 8-hour shift templates), so this script only registers the account,
or logs in when it already exists. Demand comes from the sales ingest on the demand page."""

import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

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
    parser = argparse.ArgumentParser(description="Create the ShiftOpt demo account.")
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    base_url: str = parser.parse_args().base_url.rstrip("/")
    wait_until_ready(base_url)
    sign_in(base_url, *demo_credentials())
    sys.stdout.flush()


if __name__ == "__main__":
    main()
