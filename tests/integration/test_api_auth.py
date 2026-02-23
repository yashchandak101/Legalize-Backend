"""
API integration tests: auth register and login.

Uses the test client and shared conftest session (rollback per test).
"""
import pytest


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


class TestAuthRegister:
    """POST /api/auth/register."""

    def test_register_returns_201_and_user(self, client):
        r = client.post(
            "/api/auth/register",
            json={"email": "api_user@test.example", "password": "secret123", "role": "user"},
            content_type="application/json",
        )
        assert r.status_code == 201
        data = r.get_json()
        assert "id" in data
        assert data["email"] == "api_user@test.example"

    def test_register_duplicate_email_returns_400(self, client):
        client.post(
            "/api/auth/register",
            json={"email": "dup_api@test.example", "password": "secret", "role": "user"},
            content_type="application/json",
        )
        r = client.post(
            "/api/auth/register",
            json={"email": "dup_api@test.example", "password": "other", "role": "user"},
            content_type="application/json",
        )
        assert r.status_code == 400


class TestAuthLogin:
    """POST /api/auth/login."""

    def test_login_returns_200_and_tokens(self, client):
        client.post(
            "/api/auth/register",
            json={"email": "login_api@test.example", "password": "mypass", "role": "user"},
            content_type="application/json",
        )
        r = client.post(
            "/api/auth/login",
            json={"email": "login_api@test.example", "password": "mypass"},
            content_type="application/json",
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "login_api@test.example"

    def test_login_wrong_password_returns_401(self, client):
        client.post(
            "/api/auth/register",
            json={"email": "wrong_api@test.example", "password": "right", "role": "user"},
            content_type="application/json",
        )
        r = client.post(
            "/api/auth/login",
            json={"email": "wrong_api@test.example", "password": "wrong"},
            content_type="application/json",
        )
        assert r.status_code == 401
