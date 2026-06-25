def test_healthz_needs_no_database(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_every_response_carries_a_request_id(client):
    response = client.get("/healthz")
    assert response.headers["x-request-id"]


def test_readyz_reports_the_database(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_readyz_returns_503_when_the_database_is_down(client, monkeypatch):
    import psycopg

    from regqa.api import main

    def refuse(timeout=None):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(main, "connection", refuse)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"
