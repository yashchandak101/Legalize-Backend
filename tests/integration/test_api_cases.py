"""
API integration tests: case CRUD (create, list, get, update, delete).
"""
import pytest


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
def user_tokens(client):
    _register(client, "case_user@test.example", "secret", "user")
    return _login(client, "case_user@test.example", "secret")


def _auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestCaseCreate:
    """POST /api/cases/."""

    def test_create_returns_201(self, client, user_tokens):
        r = client.post(
            "/api/cases/",
            json={"title": "My case", "description": "Full description"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 201
        data = r.get_json()
        assert data["title"] == "My case"
        assert data["description"] == "Full description"
        assert "id" in data
        assert data["user_id"] == user_tokens["user"]["id"]

    def test_create_without_token_returns_401(self, client):
        r = client.post(
            "/api/cases/",
            json={"title": "T", "description": "D"},
            content_type="application/json",
        )
        assert r.status_code == 401


class TestCaseListAndGet:
    """GET /api/cases/, GET /api/cases/<id>."""

    def test_list_returns_own_cases(self, client, user_tokens):
        client.post(
            "/api/cases/",
            json={"title": "Case one", "description": "Desc"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        r = client.get("/api/cases/", headers=_auth_headers(user_tokens))
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["title"] == "Case one" for c in data)

    def test_get_returns_case(self, client, user_tokens):
        cr = client.post(
            "/api/cases/",
            json={"title": "Get me", "description": "Desc"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        case_id = cr.get_json()["id"]
        r = client.get(f"/api/cases/{case_id}", headers=_auth_headers(user_tokens))
        assert r.status_code == 200
        assert r.get_json()["title"] == "Get me"

    def test_get_unknown_returns_404(self, client, user_tokens):
        r = client.get("/api/cases/999999", headers=_auth_headers(user_tokens))
        assert r.status_code == 404


class TestCaseUpdateAndDelete:
    """PUT /api/cases/<id>, DELETE /api/cases/<id>."""

    def test_update_returns_200(self, client, user_tokens):
        cr = client.post(
            "/api/cases/",
            json={"title": "Original", "description": "D"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        case_id = cr.get_json()["id"]
        r = client.put(
            f"/api/cases/{case_id}",
            json={"title": "Updated", "description": "New desc", "status": "closed"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 200
        assert r.get_json()["title"] == "Updated"
        assert r.get_json()["status"] == "closed"

    def test_update_invalid_status_returns_400(self, client, user_tokens):
        cr = client.post(
            "/api/cases/",
            json={"title": "S", "description": "D"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        case_id = cr.get_json()["id"]
        client.put(
            f"/api/cases/{case_id}",
            json={"status": "closed"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        r = client.put(
            f"/api/cases/{case_id}",
            json={"status": "open"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        assert r.status_code == 400
        assert r.get_json().get("code") == "INVALID_STATUS_TRANSITION"

    def test_delete_returns_200(self, client, user_tokens):
        cr = client.post(
            "/api/cases/",
            json={"title": "To delete", "description": "D"},
            headers=_auth_headers(user_tokens),
            content_type="application/json",
        )
        case_id = cr.get_json()["id"]
        r = client.delete(f"/api/cases/{case_id}", headers=_auth_headers(user_tokens))
        assert r.status_code == 200
        r2 = client.get(f"/api/cases/{case_id}", headers=_auth_headers(user_tokens))
        assert r2.status_code == 404
