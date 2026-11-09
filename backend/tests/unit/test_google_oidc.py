from urllib.parse import parse_qs, urlparse

import pytest

from src.auth import google_oidc, service
from src.exceptions import ForbiddenError, UnauthorizedError


def test_pkce_challenge_matches_rfc7636_example() -> None:
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert google_oidc.pkce_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_authorization_url_carries_state_nonce_and_s256() -> None:
    url = google_oidc.authorization_url(
        "client.apps.googleusercontent.com",
        "http://localhost:3000/api/auth/google/callback",
        "state-1",
        "nonce-1",
        "challenge-1",
    )
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.google.com"
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == ["state-1"]
    assert query["nonce"] == ["nonce-1"]
    assert query["code_challenge"] == ["challenge-1"]
    assert query["code_challenge_method"] == ["S256"]


def test_valid_claims_return_normalized_email() -> None:
    claims = {"sub": "42", "email": "Ada@Example.com", "email_verified": True, "nonce": "n"}
    assert service.validate_google_claims(claims, "n") == "ada@example.com"


def test_nonce_mismatch_is_rejected() -> None:
    claims = {"sub": "42", "email": "ada@example.com", "email_verified": True, "nonce": "other"}
    with pytest.raises(UnauthorizedError):
        service.validate_google_claims(claims, "n")


def test_unverified_google_email_is_rejected() -> None:
    claims = {"sub": "42", "email": "ada@example.com", "email_verified": False, "nonce": "n"}
    with pytest.raises(ForbiddenError):
        service.validate_google_claims(claims, "n")


def test_missing_subject_is_rejected() -> None:
    claims = {"email": "ada@example.com", "email_verified": True, "nonce": "n"}
    with pytest.raises(UnauthorizedError):
        service.validate_google_claims(claims, "n")


def test_display_name_falls_back_to_email_local_part() -> None:
    assert service.display_name_for(None, "ada@example.com") == "ada"
    assert service.display_name_for("  Ada Lovelace  ", "ada@example.com") == "Ada Lovelace"
