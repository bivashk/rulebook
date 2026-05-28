import pytest
from pydantic import ValidationError

from regqa.config import Settings


def test_missing_database_url_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env here, so nothing can supply the value
    with pytest.raises(ValidationError):
        Settings()


def test_pool_size_is_coerced_from_string(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/d")
    monkeypatch.setenv("DB_POOL_MAX", "9")
    assert Settings().db_pool_max == 9
