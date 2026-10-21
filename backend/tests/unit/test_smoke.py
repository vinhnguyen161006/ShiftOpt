from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_demand_profile_rejects_wrong_length(client: AsyncClient) -> None:
    response = await client.post(
        "/api/demand-profiles",
        json={"name": "x", "required_staff": [1, 2, 3]},
    )
    assert response.status_code == 422


async def test_shift_template_rejects_bad_start_hour(client: AsyncClient) -> None:
    response = await client.post(
        "/api/shift-templates", json={"name": "x", "start_hour": 24, "length_hours": 8}
    )
    assert response.status_code == 422
