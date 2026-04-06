from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Deliberately no default. A default here would let the process start against
    # the wrong database instead of failing loudly at line one.
    database_url: str

    log_level: str = "INFO"
    app_env: str = "local"
    db_pool_max: int = 5
    db_pool_timeout_s: float = 10.0
    readiness_timeout_s: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
