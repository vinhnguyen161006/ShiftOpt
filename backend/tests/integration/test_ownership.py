from typing import Any

import pytest
from httpx import AsyncClient

from src.auth.dependencies import SESSION_COOKIE
from src.auth.starter import EMPLOYEE_COUNT, SHIFT_TEMPLATES
from src.config import get_settings
from tests.integration.helpers import DAY_DEMAND, poll

ADA = "ada@example.com"
GRACE = "grace@example.com"


@pytest.fixture
def two_accounts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIFTOPT_ALLOWED_EMAILS", f'["{ADA}", "{GRACE}"]')
    get_settings.cache_clear()


async def sign_up(client: AsyncClient, email: str) -> str:
    client.cookies.clear()
    response = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "correct horse battery", "display_name": email},
    )
    assert response.status_code == 201
    return response.cookies[SESSION_COOKIE]


def act_as(client: AsyncClient, token: str) -> None:
    client.cookies.clear()
    client.cookies.set(SESSION_COOKIE, token)


async def solve_body(client: AsyncClient) -> dict[str, Any]:
    profile = await client.post(
        "/api/demand-profiles", json={"name": "week", "required_staff": DAY_DEMAND}
    )
    employees = (await client.get("/api/employees")).json()
    templates = (await client.get("/api/shift-templates")).json()
    return {
        "demand_profile_id": profile.json()["id"],
        "shift_template_ids": [template["id"] for template in templates],
        "employee_ids": [employee["id"] for employee in employees[:6]],
        "time_limit_seconds": 5.0,
        "relative_gap_limit": 0.01,
        "num_workers": 1,
        "random_seed": 0,
    }


async def working_data(client: AsyncClient) -> dict[str, Any]:
    body = await solve_body(client)
    run = (await client.post("/api/schedules", json=body)).json()["job_id"]
    await poll(client, f"/api/schedules/{run}")
    analysis = await client.post("/api/analysis/lp-duals", json={"solve": body, "hourly_wage": 100})
    analysis_id = analysis.json()["job_id"]
    await poll(client, f"/api/analysis/{analysis_id}")
    return {
        "body": body,
        "employee": body["employee_ids"][0],
        "template": body["shift_template_ids"][0],
        "profile": body["demand_profile_id"],
        "run": run,
        "analysis": analysis_id,
    }


async def test_new_account_gets_starter_data(
    anonymous_client: AsyncClient, two_accounts: None
) -> None:
    await sign_up(anonymous_client, ADA)
    employees = (await anonymous_client.get("/api/employees")).json()
    templates = (await anonymous_client.get("/api/shift-templates")).json()
    assert len(employees) == EMPLOYEE_COUNT
    assert {template["name"] for template in templates} == {name for name, _ in SHIFT_TEMPLATES}
    assert (await anonymous_client.get("/api/demand-profiles")).json() == []


async def test_accounts_do_not_see_each_others_data(
    anonymous_client: AsyncClient, two_accounts: None
) -> None:
    ada = await sign_up(anonymous_client, ADA)
    owned = await working_data(anonymous_client)
    await sign_up(anonymous_client, GRACE)
    for url in (
        f"/api/employees/{owned['employee']}",
        f"/api/shift-templates/{owned['template']}",
        f"/api/demand-profiles/{owned['profile']}",
        f"/api/schedules/{owned['run']}",
        f"/api/schedules/{owned['run']}/kpi",
        f"/api/analysis/{owned['analysis']}",
    ):
        assert (await anonymous_client.get(url)).status_code == 404, url
    update = await anonymous_client.put(
        f"/api/employees/{owned['employee']}",
        json={"code": "E01", "name": "taken", "hourly_wage": 100},
    )
    assert update.status_code == 404
    removal = await anonymous_client.delete(f"/api/demand-profiles/{owned['profile']}")
    assert removal.status_code == 404
    assert (await anonymous_client.get("/api/schedules")).json() == []
    assert (await anonymous_client.get("/api/demand-profiles")).json() == []
    grace_ids = {row["id"] for row in (await anonymous_client.get("/api/employees")).json()}
    assert owned["employee"] not in grace_ids
    act_as(anonymous_client, ada)
    assert (
        await anonymous_client.get(f"/api/demand-profiles/{owned['profile']}")
    ).status_code == 200


async def test_solving_with_another_accounts_inputs_is_not_found(
    anonymous_client: AsyncClient, two_accounts: None
) -> None:
    await sign_up(anonymous_client, ADA)
    ada_body = await solve_body(anonymous_client)
    await sign_up(anonymous_client, GRACE)
    grace_body = await solve_body(anonymous_client)
    foreign_profile = {**grace_body, "demand_profile_id": ada_body["demand_profile_id"]}
    foreign_shifts = {**grace_body, "shift_template_ids": ada_body["shift_template_ids"]}
    foreign_staff = {**grace_body, "employee_ids": ada_body["employee_ids"]}
    for body in (foreign_profile, foreign_shifts, foreign_staff):
        assert (await anonymous_client.post("/api/schedules", json=body)).status_code == 404


async def test_codes_are_unique_per_account(
    anonymous_client: AsyncClient, two_accounts: None
) -> None:
    employee = {"code": "X01", "name": "Shared code", "hourly_wage": 100}
    await sign_up(anonymous_client, ADA)
    assert (await anonymous_client.post("/api/employees", json=employee)).status_code == 201
    assert (await anonymous_client.post("/api/employees", json=employee)).status_code == 409
    await sign_up(anonymous_client, GRACE)
    assert (await anonymous_client.post("/api/employees", json=employee)).status_code == 201
