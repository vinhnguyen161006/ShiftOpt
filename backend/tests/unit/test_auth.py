import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from src import main
from src.auth import passwords, service, starter
from src.config import get_settings
from src.exceptions import ForbiddenError, InvalidInputError
from src.main import create_app


def test_password_hash_round_trip() -> None:
    stored = passwords.hash_password("correct horse")
    assert passwords.verify_password("correct horse", stored)
    assert not passwords.verify_password("wrong horse", stored)


def test_password_hash_is_salted() -> None:
    assert passwords.hash_password("same-password") != passwords.hash_password("same-password")


def test_verify_rejects_malformed_hash() -> None:
    assert not passwords.verify_password("x", "not-a-hash")
    assert not passwords.verify_password("x", "bcrypt$1$1$1$00$00")


def test_normalize_email_lowercases_and_trims() -> None:
    assert service.normalize_email("  Ada@Example.COM ") == "ada@example.com"


@pytest.mark.parametrize("bad", ["", "no-at-sign", "@example.com", "a@nodot", "a b@example.com"])
def test_normalize_email_rejects_invalid(bad: str) -> None:
    with pytest.raises(InvalidInputError):
        service.normalize_email(bad)


def test_allowlist_by_exact_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIFTOPT_ALLOWED_EMAILS", '["ada@example.com"]')
    get_settings.cache_clear()
    service.ensure_email_allowed("ada@example.com")
    with pytest.raises(ForbiddenError):
        service.ensure_email_allowed("grace@example.com")
    get_settings.cache_clear()


def test_allowlist_by_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIFTOPT_ALLOWED_EMAIL_DOMAINS", '["school.edu.vn"]')
    get_settings.cache_clear()
    service.ensure_email_allowed("student@school.edu.vn")
    with pytest.raises(ForbiddenError):
        service.ensure_email_allowed("student@gmail.com")
    get_settings.cache_clear()


def test_empty_allowlist_denies_everyone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIFTOPT_ALLOWED_EMAILS", raising=False)
    monkeypatch.delenv("SHIFTOPT_ALLOWED_EMAIL_DOMAINS", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ForbiddenError):
        service.ensure_email_allowed("ada@example.com")
    get_settings.cache_clear()


def test_open_signup_allows_any_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIFTOPT_ALLOWED_EMAILS", raising=False)
    monkeypatch.delenv("SHIFTOPT_ALLOWED_EMAIL_DOMAINS", raising=False)
    monkeypatch.setenv("SHIFTOPT_OPEN_SIGNUP", "true")
    get_settings.cache_clear()
    service.ensure_email_allowed("anyone@gmail.com")
    get_settings.cache_clear()


def test_starter_data_belongs_to_the_new_account() -> None:
    employees = starter.starter_employees(7)
    templates = starter.starter_templates(7)
    assert len({employee.code for employee in employees}) == starter.EMPLOYEE_COUNT
    owners = {e.owner_id for e in employees} | {t.owner_id for t in templates}
    assert owners == {7}
    part_time = {e.code: e.max_weekly_hours for e in employees if e.max_weekly_hours is not None}
    assert part_time == {starter.PART_TIME_CODE: starter.PART_TIME_WEEKLY_HOURS}
    assert [(t.name, t.start_hour) for t in templates] == list(starter.SHIFT_TEMPLATES)


def test_password_length_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIFTOPT_MIN_PASSWORD_LENGTH", "10")
    get_settings.cache_clear()
    with pytest.raises(InvalidInputError):
        service.ensure_password_strength("short")
    service.ensure_password_strength("long enough pw")
    get_settings.cache_clear()


async def test_protected_route_without_cookie_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    async def skip_recovery(session_factory: object) -> None:
        return None

    monkeypatch.setattr(main, "recover_interrupted_jobs", skip_recovery)
    application = create_app()
    async with (
        LifespanManager(application),
        AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as http,
    ):
        response = await http.get("/api/employees")
    assert response.status_code == 401


async def test_health_stays_public(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
