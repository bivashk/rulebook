import pytest
from fastapi.testclient import TestClient

from regqa.api.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    """A connection whose work is rolled back, so tests never leave rows behind."""
    from regqa.db import connection

    with connection() as conn:
        with conn.transaction(force_rollback=True):
            yield conn
