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

    raw_data_dir: str = "data/raw"

    # Defaulted, and deliberately on the slow side. If this value is wrong the
    # cost lands on someone else's server and you never see it, so the default
    # sits on the cheap side of that asymmetry.
    crawl_delay_s: float = 2.0

    # robots.txt permits everything, which means nobody has told us to stay out.
    # It does not mean the person reading their access log knows who we are.
    # Pages yielding fewer characters than this are treated as scans and sent to
    # OCR. Tuned against the char-count deciles the extract report prints.
    min_text_chars: int = 100
    ocr_dpi: int = 300

    user_agent: str = "regqa/0.1 (student project; contact: set USER_AGENT in .env)"


@lru_cache
def get_settings() -> Settings:
    return Settings()
