from typing import Any

from httpx import AsyncClient

DAY_DEMAND = [1 if 8 <= hour < 16 else 0 for hour in range(168)]
TERMINAL = ("succeeded", "failed")


def solve_body(seeded: dict[str, Any]) -> dict[str, Any]:
    return {
        "demand_profile_id": seeded["profile_id"],
        "shift_template_ids": seeded["shift_ids"],
        "time_limit_seconds": 20.0,
        "relative_gap_limit": 0.01,
        "num_workers": 1,
        "random_seed": 0,
    }


async def poll(client: AsyncClient, url: str, attempts: int = 120) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for _ in range(attempts):
        body = (await client.get(url)).json()
        if body["status"] in TERMINAL:
            return body
    raise AssertionError(f"job at {url} did not finish: {body}")
