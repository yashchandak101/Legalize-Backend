"""Health check endpoint."""
import pytest


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert "db" in data
    assert "X-Request-ID" in r.headers
