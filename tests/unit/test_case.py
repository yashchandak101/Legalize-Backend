"""
Unit tests for case CRUD: create, list by user, get by id, update, delete.

Uses real User records and the conftest session (transaction rollback per test).
"""
import pytest

from app.core.extensions import db
from app.domain.enums import RoleEnum
from app.models.user import User
from app.services.case_service import CaseService


@pytest.fixture
def case_owner():
    """A user who owns cases."""
    user = User(
        email="caseowner@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def sample_case(case_owner):
    """One case owned by case_owner."""
    return CaseService.create_case(
        user_id=case_owner.id,
        title="Test case",
        description="Description for test case",
    )


class TestCreateCase:
    """Tests for CaseService.create_case."""

    def test_creates_case_with_title_and_description(self, case_owner):
        case = CaseService.create_case(
            user_id=case_owner.id,
            title="My case",
            description="Full description",
        )
        assert case.id is not None
        assert case.title == "My case"
        assert case.description == "Full description"
        assert case.user_id == case_owner.id
        assert case.status == "open"


class TestGetUserCases:
    """Tests for CaseService.get_user_cases."""

    def test_returns_cases_for_owner(self, sample_case, case_owner):
        cases = CaseService.get_user_cases(case_owner.id)
        assert len(cases) >= 1
        assert any(c.id == sample_case.id for c in cases)

    def test_does_not_return_other_users_cases(self, sample_case, case_owner):
        other = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other)
        db.session.flush()
        cases = CaseService.get_user_cases(other.id)
        assert not any(c.id == sample_case.id for c in cases)


class TestGetCaseById:
    """Tests for CaseService.get_case_by_id."""

    def test_returns_case_by_id(self, sample_case):
        found = CaseService.get_case_by_id(sample_case.id)
        assert found is not None
        assert found.id == sample_case.id
        assert found.title == sample_case.title

    def test_returns_none_for_unknown_id(self):
        found = CaseService.get_case_by_id(999999)
        assert found is None


class TestUpdateCase:
    """Tests for CaseService.update_case."""

    def test_update_title_and_description(self, sample_case):
        updated = CaseService.update_case(
            sample_case.id,
            title="Updated title",
            description="Updated description",
        )
        assert updated.title == "Updated title"
        assert updated.description == "Updated description"

    def test_update_status(self, sample_case):
        updated = CaseService.update_case(sample_case.id, status="closed")
        assert updated.status == "closed"

    def test_update_returns_none_for_unknown_id(self):
        result = CaseService.update_case(999999, title="No")
        assert result is None

    def test_update_invalid_status_transition_raises(self, sample_case):
        from app.domain.case_rules import InvalidCaseStatusTransition
        # closed -> open not allowed
        CaseService.update_case(sample_case.id, status="closed")
        with pytest.raises(InvalidCaseStatusTransition):
            CaseService.update_case(sample_case.id, status="open")


class TestDeleteCase:
    """Tests for CaseService.delete_case."""

    def test_delete_removes_case(self, sample_case):
        case_id = sample_case.id
        result = CaseService.delete_case(case_id)
        assert result is True
        assert CaseService.get_case_by_id(case_id) is None

    def test_delete_returns_none_for_unknown_id(self):
        result = CaseService.delete_case(999999)
        assert result is None
