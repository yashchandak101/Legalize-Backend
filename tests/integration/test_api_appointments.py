"""
API integration tests: appointment endpoints (create, list, get, update status).

Uses JWT from login; client creates appointment, lawyer confirms.
"""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, email, password, role="user"):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "role": role},
        content_type="application/json",
    )
    assert r.status_code == 201
    return r.get_json()


def _login(client, email, password):
    r = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        content_type="application/json",
    )
    assert r.status_code == 200
    return r.get_json()


@pytest.fixture
def client_user_tokens(client):
    """Register a client and return login response (has access_token, user)."""
    _register(client, "appt_client@test.example", "secret", "user")
    return _login(client, "appt_client@test.example", "secret")


@pytest.fixture
def lawyer_user_tokens(client):
    """Register a lawyer and return login response."""
    _register(client, "appt_lawyer@test.example", "secret", "lawyer")
    return _login(client, "appt_lawyer@test.example", "secret")


def _auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestCreateAppointment:
    """POST /api/appointments/ (client only)."""

    def test_create_returns_201(self, client, client_user_tokens, lawyer_user_tokens):
        lawyer_id = lawyer_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        r = client.post(
            "/api/appointments/",
            json={
                "lawyer_id": lawyer_id,
                "scheduled_at": scheduled_at,
                "duration_minutes": 45,
                "notes": "API test",
            },
            headers=_auth_headers(client_user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 201
        data = r.get_json()
        assert "appointment_id" in data
        assert data["status"] == "REQUESTED"

    def test_create_without_token_returns_401(self, client, lawyer_user_tokens):
        lawyer_id = lawyer_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        r = client.post(
            "/api/appointments/",
            json={"lawyer_id": lawyer_id, "scheduled_at": scheduled_at},
            content_type="application/json",
        )
        assert r.status_code == 401

    def test_create_as_lawyer_returns_403(self, client, client_user_tokens, lawyer_user_tokens):
        # Endpoint requires role=user (client). Lawyer should get 403.
        client_id = client_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        r = client.post(
            "/api/appointments/",
            json={"lawyer_id": client_id, "scheduled_at": scheduled_at},
            headers=_auth_headers(lawyer_user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 403


class TestListAndGetAppointment:
    """GET /api/appointments/client, GET /api/appointments/<id>."""

    def test_list_client_appointments(self, client, client_user_tokens, lawyer_user_tokens):
        lawyer_id = lawyer_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post(
            "/api/appointments/",
            json={"lawyer_id": lawyer_id, "scheduled_at": scheduled_at},
            headers=_auth_headers(client_user_tokens),
            content_type="application/json",
        )
        r = client.get(
            "/api/appointments/client",
            headers=_auth_headers(client_user_tokens),
        )
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_appointment_as_client(self, client, client_user_tokens, lawyer_user_tokens):
        lawyer_id = lawyer_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cr = client.post(
            "/api/appointments/",
            json={"lawyer_id": lawyer_id, "scheduled_at": scheduled_at},
            headers=_auth_headers(client_user_tokens),
            content_type="application/json",
        )
        appt_id = cr.get_json()["appointment_id"]
        r = client.get(
            f"/api/appointments/{appt_id}",
            headers=_auth_headers(client_user_tokens),
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["id"] == appt_id
        assert data["status"] == "REQUESTED"


class TestUpdateAppointmentStatus:
    """PUT /api/appointments/<id>/status."""

    def test_lawyer_confirms_returns_200(self, client, client_user_tokens, lawyer_user_tokens):
        lawyer_id = lawyer_user_tokens["user"]["id"]
        scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        cr = client.post(
            "/api/appointments/",
            json={"lawyer_id": lawyer_id, "scheduled_at": scheduled_at},
            headers=_auth_headers(client_user_tokens),
            content_type="application/json",
        )
        appt_id = cr.get_json()["appointment_id"]
        r = client.put(
            f"/api/appointments/{appt_id}/status",
            json={"status": "CONFIRMED"},
            headers=_auth_headers(lawyer_user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "CONFIRMED"
