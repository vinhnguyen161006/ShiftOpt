from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHIFTOPT_", env_file=".env", extra="ignore")

    database_url: str = "mysql+asyncmy://shiftopt:shiftopt@localhost:3306/shiftopt?charset=utf8mb4"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    max_employees: int = 200
    max_solve_seconds: float = 300.0
    solve_workers: int = 8
    max_concurrent_jobs: int = 2
    max_pending_jobs: int = 4
    max_analysis_seconds: float = 900.0
    max_upload_bytes: int = 200 * 1024 * 1024
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    allowed_emails: list[str] = Field(default_factory=list)
    allowed_email_domains: list[str] = Field(default_factory=list)
    min_password_length: int = 8
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    post_login_redirect: str = "/demand"


@lru_cache
def get_settings() -> Settings:
    return Settings()
