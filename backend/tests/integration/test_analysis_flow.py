from typing import Any

import pytest
from httpx import AsyncClient

from tests.integration.helpers import poll, solve_body

pytestmark = pytest.mark.integration


async def test_demand_sweep_returns_one_point_per_multiplier(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    accepted = await client.post(
        "/api/analysis/demand-sweep",
        json={"solve": solve_body(seeded), "multipliers": [1.0, 1.1]},
    )
    assert accepted.status_code == 202
    run = await poll(client, f"/api/analysis/{accepted.json()['job_id']}")

    assert run["status"] == "succeeded", run["error"]
    assert [point["multiplier"] for point in run["result"]["points"]] == [1.0, 1.1]


async def test_marginal_cost_and_duals_are_labeled_approximate(
    client: AsyncClient, seeded: dict[str, Any]
) -> None:
    marginal = await client.post(
        "/api/analysis/marginal-cost",
        json={"solve": solve_body(seeded), "hourly_wage": 100},
    )
    marginal_run = await poll(client, f"/api/analysis/{marginal.json()['job_id']}")
    assert marginal_run["status"] == "succeeded", marginal_run["error"]
    assert len(marginal_run["result"]["marginal_cost_by_hour"]) == 168
    assert marginal_run["result"]["approximate"] is True

    duals = await client.post(
        "/api/analysis/lp-duals",
        json={"solve": solve_body(seeded), "hourly_wage": 100},
    )
    duals_run = await poll(client, f"/api/analysis/{duals.json()['job_id']}")
    assert duals_run["status"] == "succeeded", duals_run["error"]
    assert len(duals_run["result"]["duals_by_hour"]) == 168
    assert duals_run["result"]["approximate"] is True


async def test_sweep_rejects_too_many_points(client: AsyncClient, seeded: dict[str, Any]) -> None:
    response = await client.post(
        "/api/analysis/demand-sweep",
        json={"solve": solve_body(seeded), "multipliers": [1.0] * 21},
    )
    assert response.status_code == 422
