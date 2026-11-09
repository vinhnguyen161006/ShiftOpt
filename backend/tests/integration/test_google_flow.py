from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient

from src.auth import google_oidc
from src.auth.dependencies import SESSION_COOKIE
from src.config import get_settings

CLIENT_ID = "test-client.apps.googleusercontent.com"
REDIRECT_URI = "http://test/api/auth/google/callback"


@pytest.fixture
def google_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIFTOPT_GOOGLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("SHIFTOPT_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("SHIFTOPT_GOOGLE_REDIRECT_URI", REDIRECT_URI)
    get_settings.cache_clear()


def query_of(location: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(location).query)


async def start(client: AsyncClient) -> dict[str, list[str]]:
    response = await client.get("/api/auth/google/start")
    assert response.status_code == 302
    return query_of(response.headers["location"])


async def test_start_without_configuration_redirects_with_reason(
    anonymous_client: AsyncClient,
) -> None:
    response = await anonymous_client.get("/api/auth/google/start")
    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=not_configured"


async def test_start_redirects_to_google_with_pkce(
    anonymous_client: AsyncClient, google_configured: None
) -> None:
    query = await start(anonymous_client)
    assert query["client_id"] == [CLIENT_ID]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert len(query["state"][0]) > 20
    assert len(query["nonce"][0]) > 20


async def test_callback_with_unknown_state_is_rejected(
    anonymous_client: AsyncClient, google_configured: None
) -> None:
    response = await anonymous_client.get(
        "/api/auth/google/callback", params={"state": "forged", "code": "abc"}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=google_failed"
    assert SESSION_COOKIE not in response.cookies


async def test_callback_denied_by_user(
    anonymous_client: AsyncClient, google_configured: None
) -> None:
    response = await anonymous_client.get(
        "/api/auth/google/callback", params={"error": "access_denied", "state": "x"}
    )
    assert response.headers["location"] == "/login?error=google_denied"


async def test_state_is_single_use(
    anonymous_client: AsyncClient, google_configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    query = await start(anonymous_client)
    state = query["state"][0]
    nonce = query["nonce"][0]
    monkeypatch.setattr(google_oidc, "exchange_code", lambda *_args, **_kwargs: "id-token")
    monkeypatch.setattr(
        google_oidc,
        "verify_id_token",
        lambda *_args, **_kwargs: claims("ada@example.com", nonce),
    )
    first = await anonymous_client.get(
        "/api/auth/google/callback", params={"state": state, "code": "abc"}
    )
    assert first.headers["location"] == "/demand"
    anonymous_client.cookies.clear()
    replay = await anonymous_client.get(
        "/api/auth/google/callback", params={"state": state, "code": "abc"}
    )
    assert replay.headers["location"] == "/login?error=google_failed"


async def test_successful_google_login_creates_session(
    anonymous_client: AsyncClient, google_configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    query = await start(anonymous_client)
    monkeypatch.setattr(google_oidc, "exchange_code", lambda *_args, **_kwargs: "id-token")
    monkeypatch.setattr(
        google_oidc,
        "verify_id_token",
        lambda *_args, **_kwargs: claims("ada@example.com", query["nonce"][0]),
    )
    callback = await anonymous_client.get(
        "/api/auth/google/callback", params={"state": query["state"][0], "code": "abc"}
    )
    assert callback.status_code == 302
    assert SESSION_COOKIE in callback.cookies
    me = await anonymous_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"


async def test_google_email_outside_allowlist_is_refused(
    anonymous_client: AsyncClient, google_configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    query = await start(anonymous_client)
    monkeypatch.setattr(google_oidc, "exchange_code", lambda *_args, **_kwargs: "id-token")
    monkeypatch.setattr(
        google_oidc,
        "verify_id_token",
        lambda *_args, **_kwargs: claims("eve@example.com", query["nonce"][0]),
    )
    callback = await anonymous_client.get(
        "/api/auth/google/callback", params={"state": query["state"][0], "code": "abc"}
    )
    assert callback.headers["location"] == "/login?error=not_allowed"
    assert SESSION_COOKIE not in callback.cookies


def claims(email: str, nonce: str) -> dict[str, Any]:
    return {
        "sub": "google-subject-1",
        "email": email,
        "email_verified": True,
        "nonce": nonce,
        "name": "Ada Lovelace",
    }
