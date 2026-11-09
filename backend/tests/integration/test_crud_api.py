from datetime import date, timedelta

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


def _hourly_csv(store: str = "7") -> bytes:
    rows = [
        f"{store},{(date(2024, 6, 3) + timedelta(days=day)).isoformat()} {hour:02d}:00:00,8.0"
        for day in range(7)
        for hour in range(24)
    ]
    return "\n".join(["cua_hang,thoi_diem,doanh_thu", *rows]).encode()


async def test_ingest_sales_file_derives_profile(client: AsyncClient) -> None:
    params: dict[str, str | int | float] = {
        "name": "uploaded",
        "date_column": "thoi_diem",
        "sales_column": "doanh_thu",
        "store_column": "cua_hang",
        "store": "7",
        "productivity": 4,
        "night_min_staff": 2,
    }
    response = await client.post(
        "/api/demand-profiles/ingest",
        params=params,
        content=_hourly_csv(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "sales"
    assert body["has_sales_load"] is True
    assert body["required_staff"][12] == 2
    assert body["required_staff"][0] == 2
    assert body["source_metadata"]["store"] == "7"
    assert len(body["source_metadata"]["sha256"]) == 64
    assert body["conversion_params"]["productivity"] == 4


async def test_inspect_sales_file_guesses_mapping(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/ingest/inspect",
        content=_hourly_csv(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["format"] == "csv"
    assert body["rows"] == 168
    assert body["guess"]["date_column"] == "thoi_diem"
    assert body["guess"]["sales_column"] == "doanh_thu"
    assert body["stores"] == ["7"]


async def test_ingest_rejects_unreadable_file(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/ingest",
        params={"name": "bad", "date_column": "x", "sales_column": "y"},
        content=b"",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 422


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


async def test_employee_csv_import_is_all_or_nothing(client: AsyncClient) -> None:
    good = "code,name,hourly_wage,unavailable_days\nC1,Ada,100,CN\nC2,Grace,110,\n"
    imported = await client.post("/api/employees/from-csv", json={"csv_text": good})
    assert imported.status_code == 201
    assert [row["code"] for row in imported.json()] == ["C1", "C2"]
    assert imported.json()[0]["unavailable_days"] == [6]
    again = await client.post("/api/employees/from-csv", json={"csv_text": good})
    assert again.status_code == 409
    bad = "code,name,hourly_wage\nC3,Linus,100\nC4,Ken,zero\n"
    rejected = await client.post("/api/employees/from-csv", json={"csv_text": bad})
    assert rejected.status_code == 422
    assert "row 3" in rejected.text
    codes = [row["code"] for row in (await client.get("/api/employees")).json()]
    assert codes == ["C1", "C2"]
