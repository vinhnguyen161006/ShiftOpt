import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import google_oidc
from src.auth.models import AuthSessionRecord, OAuthTransactionRecord, UserRecord
from src.auth.passwords import hash_password, verify_password
from src.config import get_settings
from src.database import commit_unique
from src.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidInputError,
    ServiceUnavailableError,
    UnauthorizedError,
)

INVALID_CREDENTIALS = "invalid email or password"
DUPLICATE_EMAIL = "an account with this email already exists"
EMAIL_NOT_ALLOWED = "this email is not allowed to use ShiftOpt"
LENGTH_RULE_MESSAGE = "password must be at least {minimum} characters"
INVALID_EMAIL = "email is not valid"
TOKEN_BYTES = 32
OAUTH_TTL_MINUTES = 10
GOOGLE_NOT_CONFIGURED = "google sign-in is not configured"
GOOGLE_EXPIRED = "google sign-in expired, try again"
GOOGLE_EMAIL_UNVERIFIED = "google email is not verified"
GOOGLE_ACCOUNT_CONFLICT = "this email is linked to another google account"
ACCOUNT_DISABLED = "this account is disabled"
MAX_DISPLAY_NAME = 120
DUMMY_HASH = hash_password("shiftopt-timing-equalizer")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    local, separator, domain = normalized.partition("@")
    if not local or not separator or "." not in domain or " " in normalized:
        raise InvalidInputError(INVALID_EMAIL)
    return normalized


def ensure_email_allowed(email: str) -> None:
    settings = get_settings()
    domain = email.rpartition("@")[2]
    if email in settings.allowed_emails or domain in settings.allowed_email_domains:
        return
    raise ForbiddenError(EMAIL_NOT_ALLOWED)


def ensure_password_strength(password: str) -> None:
    minimum = get_settings().min_password_length
    if len(password) < minimum:
        raise InvalidInputError(LENGTH_RULE_MESSAGE.format(minimum=minimum))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def register(
    session: AsyncSession, email: str, password: str, display_name: str
) -> UserRecord:
    normalized = normalize_email(email)
    ensure_email_allowed(normalized)
    ensure_password_strength(password)
    user = UserRecord(
        email=normalized,
        password_hash=hash_password(password),
        display_name=display_name.strip(),
    )
    session.add(user)
    await commit_unique(session, DUPLICATE_EMAIL)
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> UserRecord:
    normalized = normalize_email(email)
    user = await session.scalar(select(UserRecord).where(UserRecord.email == normalized))
    stored = user.password_hash if user is not None else None
    password_ok = verify_password(password, stored or DUMMY_HASH)
    if user is None or stored is None or user.disabled or not password_ok:
        raise UnauthorizedError(INVALID_CREDENTIALS)
    ensure_email_allowed(normalized)
    return user


async def open_session(session: AsyncSession, user: UserRecord) -> str:
    token = secrets.token_urlsafe(TOKEN_BYTES)
    ttl = timedelta(hours=get_settings().session_ttl_hours)
    session.add(
        AuthSessionRecord(
            id=hash_token(token),
            user_id=user.id,
            expires_at=utc_now() + ttl,
        )
    )
    await session.commit()
    return token


async def resolve_session(session: AsyncSession, token: str | None) -> UserRecord:
    if not token:
        raise UnauthorizedError("login required")
    row = await session.scalar(
        select(AuthSessionRecord).where(AuthSessionRecord.id == hash_token(token))
    )
    if row is None or row.expires_at <= utc_now():
        raise UnauthorizedError("login required")
    user = await session.get(UserRecord, row.user_id)
    if user is None or user.disabled:
        raise UnauthorizedError("login required")
    return user


async def close_session(session: AsyncSession, token: str | None) -> None:
    if not token:
        return
    row = await session.get(AuthSessionRecord, hash_token(token))
    if row is not None:
        await session.delete(row)
        await session.commit()


def ensure_google_configured() -> None:
    settings = get_settings()
    if not (
        settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri
    ):
        raise ServiceUnavailableError(GOOGLE_NOT_CONFIGURED)


async def start_google_login(session: AsyncSession) -> str:
    ensure_google_configured()
    settings = get_settings()
    state = secrets.token_urlsafe(TOKEN_BYTES)
    nonce = secrets.token_urlsafe(TOKEN_BYTES)
    verifier = secrets.token_urlsafe(64)
    now = utc_now()
    await session.execute(
        delete(OAuthTransactionRecord).where(OAuthTransactionRecord.expires_at <= now)
    )
    session.add(
        OAuthTransactionRecord(
            id=hash_token(state),
            nonce=nonce,
            code_verifier=verifier,
            expires_at=now + timedelta(minutes=OAUTH_TTL_MINUTES),
        )
    )
    await session.commit()
    return google_oidc.authorization_url(
        settings.google_client_id,
        settings.google_redirect_uri,
        state,
        nonce,
        google_oidc.pkce_challenge(verifier),
    )


async def finish_google_login(session: AsyncSession, code: str, state: str) -> UserRecord:
    ensure_google_configured()
    settings = get_settings()
    transaction = await session.get(OAuthTransactionRecord, hash_token(state))
    if transaction is None:
        raise UnauthorizedError(GOOGLE_EXPIRED)
    await session.delete(transaction)
    await session.commit()
    if transaction.expires_at <= utc_now():
        raise UnauthorizedError(GOOGLE_EXPIRED)
    transport = google_oidc.StdlibTransport()
    id_token = google_oidc.exchange_code(
        code,
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
        transaction.code_verifier,
        transport,
    )
    claims = google_oidc.verify_id_token(id_token, settings.google_client_id, transport)
    email = validate_google_claims(claims, transaction.nonce)
    ensure_email_allowed(email)
    return await upsert_google_user(session, str(claims["sub"]), email, claims.get("name"))


def validate_google_claims(claims: dict[str, object], expected_nonce: str) -> str:
    if claims.get("nonce") != expected_nonce:
        raise UnauthorizedError(google_oidc.GOOGLE_FAILED)
    if claims.get("email_verified") is not True:
        raise ForbiddenError(GOOGLE_EMAIL_UNVERIFIED)
    subject = claims.get("sub")
    email = claims.get("email")
    if not isinstance(subject, str) or not subject or not isinstance(email, str):
        raise UnauthorizedError(google_oidc.GOOGLE_FAILED)
    return normalize_email(email)


async def upsert_google_user(
    session: AsyncSession, subject: str, email: str, name: object
) -> UserRecord:
    user = await session.scalar(select(UserRecord).where(UserRecord.google_sub == subject))
    if user is None:
        user = await session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None:
            user = UserRecord(
                email=email,
                password_hash=None,
                google_sub=subject,
                display_name=display_name_for(name, email),
            )
            session.add(user)
        elif user.google_sub is None:
            user.google_sub = subject
        elif user.google_sub != subject:
            raise ConflictError(GOOGLE_ACCOUNT_CONFLICT)
    if user.disabled:
        raise ForbiddenError(ACCOUNT_DISABLED)
    await commit_unique(session, DUPLICATE_EMAIL)
    await session.refresh(user)
    return user


def display_name_for(name: object, email: str) -> str:
    candidate = name.strip() if isinstance(name, str) else ""
    fallback = email.partition("@")[0]
    return (candidate or fallback)[:MAX_DISPLAY_NAME]
