from datetime import date, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
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


async def test_demand_from_dataset_missing_store_is_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/from-dataset", json={"name": "store", "store_id": 999999}
    )
    assert response.status_code == 404


def _sales_file(path: Path) -> bytes:
    rows = [
        {
            "store_id": 7,
            "product_id": 1,
            "dt": (date(2024, 6, 3) + timedelta(days=day)).isoformat(),
            "hours_sale": [8.0] * 24,
            "hours_stock_status": [0] * 24,
        }
        for day in range(7)
    ]
    pq.write_table(pa.Table.from_pylist(rows), path)
    return path.read_bytes()


async def test_demand_from_uploaded_sales(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SHIFTOPT_DATASET_DIR", str(tmp_path / "processed"))
    get_settings.cache_clear()
    params: dict[str, str | int] = {
        "name": "uploaded",
        "store_id": 7,
        "productivity": 4,
        "night_min_staff": 2,
    }
    response = await client.post(
        "/api/demand-profiles/ingest",
        params=params,
        content=_sales_file(tmp_path / "train.parquet"),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["required_staff"][12] == 2
    assert body["required_staff"][0] == 2
    assert body["source_metadata"]["store_id"] == "7"
    assert body["source_metadata"]["source"].startswith("uploaded sales file, sha256 ")
    assert body["conversion_params"]["productivity"] == 4


async def test_demand_upload_rejects_non_parquet(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles/ingest",
        params={"name": "bad", "store_id": 7},
        content=b"date,hour,sales",
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
