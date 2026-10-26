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
    dataset_dir: str = "../data/processed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
