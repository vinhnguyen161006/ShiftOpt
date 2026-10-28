import pytest
from httpx import AsyncClient

from src.config import get_settings
from tests.integration.helpers import DAY_DEMAND

pytestmark = pytest.mark.integration


async def test_employee_crud_and_conflicts(client: AsyncClient) -> None:
    created = await client.post(
        "/api/employees",
        json={"code": "E1", "name": "Ann", "hourly_wage": 100, "unavailable_days": [6, 2]},
    )
    assert created.status_code == 201
    assert created.json()["unavailable_days"] == [2, 6]

    duplicate = await client.post(
        "/api/employees", json={"code": "E1", "name": "Bob", "hourly_wage": 90}
    )
    assert duplicate.status_code == 409

    employee_id = created.json()["id"]
    updated = await client.put(
        f"/api/employees/{employee_id}",
        json={"code": "E1", "name": "Ann", "hourly_wage": 110, "preferred_days_off": [5]},
    )
    assert updated.status_code == 200
    assert updated.json()["hourly_wage"] == 110

    assert (await client.delete(f"/api/employees/{employee_id}")).status_code == 204
    assert (await client.get(f"/api/employees/{employee_id}")).status_code == 404


async def test_employee_rejects_repeated_request_day(client: AsyncClient) -> None:
    response = await client.post(
        "/api/employees",
        json={"code": "E9", "name": "Dup", "hourly_wage": 100, "unavailable_days": [1, 1]},
    )
    assert response.status_code == 422


async def test_employee_limit_is_enforced(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SHIFTOPT_MAX_EMPLOYEES", "1")
    get_settings.cache_clear()
    await client.post("/api/employees", json={"code": "A", "name": "A", "hourly_wage": 100})
    response = await client.post(
        "/api/employees", json={"code": "B", "name": "B", "hourly_wage": 100}
    )
    assert response.status_code == 422


async def test_shift_template_rejects_length_above_daily_limit(client: AsyncClient) -> None:
    response = await client.post(
        "/api/shift-templates", json={"name": "long", "start_hour": 6, "length_hours": 10}
    )
    assert response.status_code == 422


async def test_shift_template_crud(client: AsyncClient) -> None:
    created = await client.post(
        "/api/shift-templates", json={"name": "day", "start_hour": 8, "length_hours": 8}
    )
    assert created.status_code == 201
    template_id = created.json()["id"]
    duplicate = await client.post(
        "/api/shift-templates", json={"name": "day", "start_hour": 9, "length_hours": 8}
    )
    assert duplicate.status_code == 409
    updated = await client.put(
        f"/api/shift-templates/{template_id}",
        json={"name": "day", "start_hour": 9, "length_hours": 7},
    )
    assert updated.status_code == 200
    assert (await client.delete(f"/api/shift-templates/{template_id}")).status_code == 204


async def test_demand_from_csv_accepts_grid_and_rejects_short_grid(client: AsyncClient) -> None:
    rows = "\n".join(
        ",".join(str(value) for value in DAY_DEMAND[day * 24 : day * 24 + 24]) for day in range(7)
    )
    created = await client.post(
        "/api/demand-profiles/from-csv", json={"name": "csv", "csv_text": rows}
    )
    assert created.status_code == 201
    assert created.json()["source"] == "csv"

    short = await client.post(
        "/api/demand-profiles/from-csv", json={"name": "short", "csv_text": "1,2,3"}
    )
    assert short.status_code == 422


async def test_demand_from_call_center_uses_erlang_a(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/from-call-center",
        json={
            "name": "calls",
            "base_rate": 40,
            "handle_seconds": 180,
            "patience_seconds": 60,
            "seed": 0,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["mode"] == "erlang"
    assert len(body["required_staff"]) == 168
    assert "simulated" in body["source_metadata"]["label"]


async def test_demand_from_dataset_missing_store_is_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/from-dataset", json={"name": "store", "store_id": 999999}
    )
    assert response.status_code == 404


async def test_demand_profile_update_and_delete(client: AsyncClient) -> None:
    created = await client.post(
        "/api/demand-profiles", json={"name": "week", "required_staff": DAY_DEMAND}
    )
    profile_id = created.json()["id"]
    updated = await client.put(
        f"/api/demand-profiles/{profile_id}",
        json={"name": "week", "required_staff": [0] * 168},
    )
    assert updated.status_code == 200
    assert updated.json()["required_staff"][0] == 0
    assert (await client.delete(f"/api/demand-profiles/{profile_id}")).status_code == 204
    assert (await client.get(f"/api/demand-profiles/{profile_id}")).status_code == 404
