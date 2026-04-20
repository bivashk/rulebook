import pytest
from fastapi.testclient import TestClient

from regqa.api.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
