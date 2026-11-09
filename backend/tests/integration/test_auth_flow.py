from httpx import AsyncClient

from src.auth.dependencies import SESSION_COOKIE


async def test_register_sets_cookie_and_me_works(anonymous_client: AsyncClient) -> None:
    registered = await anonymous_client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "correct horse", "display_name": "Ada"},
    )
    assert registered.status_code == 201
    assert SESSION_COOKIE in registered.cookies
    me = await anonymous_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"
    employees = await anonymous_client.get("/api/employees")
    assert employees.status_code == 200


async def test_login_wrong_password_is_generic(anonymous_client: AsyncClient) -> None:
    await anonymous_client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "correct horse", "display_name": "Ada"},
    )
    await anonymous_client.post("/api/auth/logout")
    wrong = await anonymous_client.post(
        "/api/auth/login", json={"email": "ada@example.com", "password": "nope-nope"}
    )
    unknown = await anonymous_client.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": "nope-nope"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_register_rejects_email_outside_allowlist(anonymous_client: AsyncClient) -> None:
    response = await anonymous_client.post(
        "/api/auth/register",
        json={"email": "eve@example.com", "password": "correct horse", "display_name": "Eve"},
    )
    assert response.status_code == 403


async def test_logout_invalidates_cookie(anonymous_client: AsyncClient) -> None:
    await anonymous_client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "correct horse", "display_name": "Ada"},
    )
    token = anonymous_client.cookies.get(SESSION_COOKIE)
    assert token is not None
    await anonymous_client.post("/api/auth/logout")
    anonymous_client.cookies.clear()
    anonymous_client.cookies.set(SESSION_COOKIE, token)
    response = await anonymous_client.get("/api/employees")
    assert response.status_code == 401
