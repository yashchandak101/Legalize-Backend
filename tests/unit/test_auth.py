"""
Unit tests for auth: register and login.

Uses the shared conftest session (transaction rollback per test).
"""
import pytest

from app.domain.enums import RoleEnum
from app.services.auth_service import AuthService


class TestRegister:
    """Tests for AuthService.register."""

    def test_register_creates_user_with_valid_role(self):
        user = AuthService.register(
            email="newuser@test.example",
            password="secret123",
            role=RoleEnum.USER.value,
        )
        assert user.id is not None
        assert user.email == "newuser@test.example"
        assert user.role == RoleEnum.USER.value
        assert user.password != "secret123"

    def test_register_accepts_lawyer_role(self):
        user = AuthService.register(
            email="lawyer@test.example",
            password="secret123",
            role=RoleEnum.LAWYER.value,
        )
        assert user.role == RoleEnum.LAWYER.value

    def test_register_accepts_admin_role(self):
        user = AuthService.register(
            email="admin@test.example",
            password="secret123",
            role=RoleEnum.ADMIN.value,
        )
        assert user.role == RoleEnum.ADMIN.value

    def test_register_raises_on_duplicate_email(self):
        AuthService.register(
            email="dup@test.example",
            password="secret123",
            role=RoleEnum.USER.value,
        )
        with pytest.raises(ValueError, match="already registered"):
            AuthService.register(
                email="dup@test.example",
                password="other",
                role=RoleEnum.USER.value,
            )

    def test_register_raises_on_invalid_role(self):
        with pytest.raises(ValueError, match="Invalid role"):
            AuthService.register(
                email="bad@test.example",
                password="secret123",
                role="superuser",
            )


class TestLogin:
    """Tests for AuthService.login."""

    def test_login_returns_tokens_and_user(self):
        AuthService.register(
            email="login@test.example",
            password="mypassword",
            role=RoleEnum.USER.value,
        )
        result = AuthService.login(email="login@test.example", password="mypassword")
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["email"] == "login@test.example"
        assert result["user"]["role"] == RoleEnum.USER.value
        assert result["user"]["id"] is not None

    def test_login_raises_on_wrong_password(self):
        AuthService.register(
            email="wrongpw@test.example",
            password="correct",
            role=RoleEnum.USER.value,
        )
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login(email="wrongpw@test.example", password="wrong")

    def test_login_raises_on_unknown_email(self):
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login(email="nobody@test.example", password="any")
