import base64
import hashlib
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from google.oauth2 import id_token as google_id_token

from src.exceptions import UnauthorizedError

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_EXCHANGE_URL = "https://oauth2.googleapis.com/token"
SCOPES = "openid email profile"
REQUEST_TIMEOUT_SECONDS = 10.0
GOOGLE_FAILED = "google sign-in failed"
CLOCK_SKEW_SECONDS = 10
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransportResponse:
    status: int
    data: bytes
    headers: dict[str, str]


class StdlibTransport:
    """Callable with the shape google-auth expects, built on urllib so no HTTP package is added."""

    def __call__(
        self,
        url: str,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        **_: Any,
    ) -> TransportResponse:
        request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return _to_response(response.status, response.read(), response.headers.items())
        except urllib.error.HTTPError as error:
            return _to_response(error.code, error.read(), error.headers.items())


def _to_response(status: int, data: bytes, headers: Any) -> TransportResponse:
    return TransportResponse(status, data, {key.lower(): value for key, value in headers})


def pkce_challenge(verifier: str) -> str:
    """S256 code challenge from RFC 7636, section 4.2."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def authorization_url(
    client_id: str, redirect_uri: str, state: str, nonce: str, code_challenge: str
) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
    )
    return f"{AUTHORIZATION_ENDPOINT}?{query}"


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str,
    transport: StdlibTransport,
) -> str:
    body = urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
    ).encode("ascii")
    response = transport(
        GOOGLE_EXCHANGE_URL,
        method="POST",
        body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    payload = _json_object(response.data)
    token = payload.get("id_token")
    if response.status != 200 or not isinstance(token, str):
        logger.warning(
            "google token exchange rejected: status=%s error=%s description=%s",
            response.status,
            payload.get("error"),
            payload.get("error_description"),
        )
        raise UnauthorizedError(GOOGLE_FAILED)
    return token


def verify_id_token(token: str, client_id: str, transport: StdlibTransport) -> dict[str, Any]:
    """Checks signature, issuer, audience and expiry through google-auth."""
    try:
        claims = google_id_token.verify_oauth2_token(
            token,
            transport,
            audience=client_id,
            clock_skew_in_seconds=CLOCK_SKEW_SECONDS,
        )
    except ValueError as error:
        logger.warning("google id token rejected: %s", error)
        raise UnauthorizedError(GOOGLE_FAILED) from error
    return dict(claims)


def _json_object(data: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(data or b"{}")
    except json.JSONDecodeError as error:
        raise UnauthorizedError(GOOGLE_FAILED) from error
    return parsed if isinstance(parsed, dict) else {}
