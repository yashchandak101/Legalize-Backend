"""
Unit tests for appointment creation, retrieval, listing, status updates, and permissions.

Uses real User records (client and lawyer) so that foreign keys and role-based
logic are exercised correctly. DB session is rolled back after each test (conftest).
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.core.extensions import db
from app.domain.enums import RoleEnum
from app.models.appointment import Appointment
from app.models.user import User
from app.services.appointment_service import AppointmentService


# -----------------------------------------------------------------------------
# Fixtures: users and appointments
# -----------------------------------------------------------------------------


@pytest.fixture
def client_user():
    """A user with role=user (client) for booking appointments."""
    user = User(
        email="client@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def lawyer_user():
    """A user with role=lawyer for being assigned to appointments."""
    user = User(
        email="lawyer@test.example",
        password="hashed",
        role=RoleEnum.LAWYER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def appointment(client_user, lawyer_user):
    """One REQUESTED appointment in the future (client_user + lawyer_user)."""
    scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
    return AppointmentService.create_appointment(
        client_id=client_user.id,
        lawyer_id=lawyer_user.id,
        scheduled_at=scheduled_at,
        duration_minutes=60,
        notes="Fixture appointment",
        meeting_link="https://meet.example.com/fixture",
    )


def _future_time(days_ahead: int = 1):
    return datetime.now(timezone.utc) + timedelta(days=days_ahead)


# -----------------------------------------------------------------------------
# Create
# -----------------------------------------------------------------------------


class TestCreateAppointment:
    """Tests for AppointmentService.create_appointment."""

    def test_creates_with_default_status_requested(self, client_user, lawyer_user):
        scheduled_at = _future_time(2)
        appt = AppointmentService.create_appointment(
            client_id=client_user.id,
            lawyer_id=lawyer_user.id,
            scheduled_at=scheduled_at,
            duration_minutes=45,
            notes="New appointment",
            meeting_link="https://meet.example.com/new",
        )
        assert appt.id is not None
        assert appt.status == Appointment.STATUS_REQUESTED
        assert appt.client_id == client_user.id
        assert appt.lawyer_id == lawyer_user.id
        assert appt.duration_minutes == 45
        assert appt.notes == "New appointment"
        assert appt.meeting_link == "https://meet.example.com/new"
        # DB may return naive datetime; compare as timestamps or normalize
        assert appt.scheduled_at.replace(tzinfo=timezone.utc) == scheduled_at

    def test_creates_with_minimal_args(self, client_user, lawyer_user):
        scheduled_at = _future_time(1)
        appt = AppointmentService.create_appointment(
            client_id=client_user.id,
            lawyer_id=lawyer_user.id,
            scheduled_at=scheduled_at,
        )
        assert appt.id is not None
        assert appt.status == Appointment.STATUS_REQUESTED
        assert appt.duration_minutes == 30
        assert appt.notes is None
        assert appt.meeting_link is None


# -----------------------------------------------------------------------------
# Get
# -----------------------------------------------------------------------------


class TestGetAppointment:
    """Tests for AppointmentService.get_appointment."""

    def test_returns_appointment_by_id(self, appointment):
        found = AppointmentService.get_appointment(str(appointment.id))
        assert found.id == appointment.id
        assert found.notes == appointment.notes
        assert found.client_id == appointment.client_id

    def test_raises_when_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            AppointmentService.get_appointment("00000000-0000-0000-0000-000000000000")


# -----------------------------------------------------------------------------
# List
# -----------------------------------------------------------------------------


class TestListAppointments:
    """Tests for list_appointments_for_client and list_appointments_for_lawyer."""

    def test_list_for_client_includes_own_appointment(self, appointment, client_user):
        results = AppointmentService.list_appointments_for_client(client_user.id)
        assert len(results) >= 1
        ids = [a.id for a in results]
        assert appointment.id in ids

    def test_list_for_client_filter_by_status(self, appointment, client_user):
        requested = AppointmentService.list_appointments_for_client(
            client_user.id, status=Appointment.STATUS_REQUESTED
        )
        assert any(a.id == appointment.id for a in requested)

        confirmed = AppointmentService.list_appointments_for_client(
            client_user.id, status=Appointment.STATUS_CONFIRMED
        )
        assert not any(a.id == appointment.id for a in confirmed)

    def test_list_for_lawyer_includes_own_appointment(self, appointment, lawyer_user):
        results = AppointmentService.list_appointments_for_lawyer(lawyer_user.id)
        assert len(results) >= 1
        assert any(a.id == appointment.id for a in results)

    def test_list_for_lawyer_filter_by_status(self, appointment, lawyer_user):
        requested = AppointmentService.list_appointments_for_lawyer(
            lawyer_user.id, status=Appointment.STATUS_REQUESTED
        )
        assert any(a.id == appointment.id for a in requested)


# -----------------------------------------------------------------------------
# Update status: valid transitions
# -----------------------------------------------------------------------------


class TestUpdateStatusValidTransitions:
    """Tests for allowed status transitions and role-based updates."""

    def test_lawyer_can_confirm_requested(self, appointment, lawyer_user):
        updated = AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        assert updated.status == Appointment.STATUS_CONFIRMED

    def test_lawyer_can_complete_confirmed(self, appointment, lawyer_user):
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        updated = AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_COMPLETED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        assert updated.status == Appointment.STATUS_COMPLETED

    def test_lawyer_can_cancel_requested(self, appointment, lawyer_user):
        updated = AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CANCELLED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        assert updated.status == Appointment.STATUS_CANCELLED

    def test_client_can_cancel_requested(self, appointment, client_user):
        updated = AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CANCELLED,
            actor_role=RoleEnum.USER,
            actor_id=client_user.id,
        )
        assert updated.status == Appointment.STATUS_CANCELLED

    def test_client_can_cancel_confirmed(self, appointment, client_user):
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=appointment.lawyer_id,
        )
        updated = AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CANCELLED,
            actor_role=RoleEnum.USER,
            actor_id=client_user.id,
        )
        assert updated.status == Appointment.STATUS_CANCELLED


# -----------------------------------------------------------------------------
# Update status: invalid transitions and permissions
# -----------------------------------------------------------------------------


class TestUpdateStatusInvalidTransition:
    """Invalid status transitions must raise ValueError."""

    def test_requested_to_completed_disallowed(self, appointment, lawyer_user):
        with pytest.raises(ValueError, match="Cannot change appointment status"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_COMPLETED,
                actor_role=RoleEnum.LAWYER,
                actor_id=lawyer_user.id,
            )

    def test_confirmed_to_requested_disallowed(self, appointment, lawyer_user):
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        with pytest.raises(ValueError, match="Cannot change appointment status"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_REQUESTED,
                actor_role=RoleEnum.LAWYER,
                actor_id=lawyer_user.id,
            )

    def test_completed_unchanged(self, appointment, lawyer_user):
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_COMPLETED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        with pytest.raises(ValueError, match="Cannot change appointment status"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_CANCELLED,
                actor_role=RoleEnum.LAWYER,
                actor_id=lawyer_user.id,
            )


class TestUpdateStatusPermissions:
    """Role and ownership checks for update_status."""

    def test_client_cannot_confirm(self, appointment, client_user):
        with pytest.raises(PermissionError, match="only cancel"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_CONFIRMED,
                actor_role=RoleEnum.USER,
                actor_id=client_user.id,
            )

    def test_client_cannot_modify_other_clients_appointment(
        self, appointment, client_user, lawyer_user
    ):
        # Create another client and try to cancel the first client's appointment
        other_client = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_client)
        db.session.flush()
        with pytest.raises(PermissionError, match="cannot modify another"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_CANCELLED,
                actor_role=RoleEnum.USER,
                actor_id=other_client.id,
            )

    def test_lawyer_cannot_modify_other_lawyers_appointment(
        self, appointment, lawyer_user, client_user
    ):
        other_lawyer = User(
            email="otherlawyer@test.example",
            password="hashed",
            role=RoleEnum.LAWYER.value,
        )
        db.session.add(other_lawyer)
        db.session.flush()
        with pytest.raises(PermissionError, match="cannot modify another"):
            AppointmentService.update_status(
                appointment_id=str(appointment.id),
                new_status=Appointment.STATUS_CONFIRMED,
                actor_role=RoleEnum.LAWYER,
                actor_id=other_lawyer.id,
            )


# -----------------------------------------------------------------------------
# Cancel (convenience)
# -----------------------------------------------------------------------------


class TestCancelAppointment:
    """Tests for AppointmentService.cancel_appointment."""

    def test_cancel_returns_cancelled_appointment(self, appointment, client_user):
        updated = AppointmentService.cancel_appointment(
            appointment_id=str(appointment.id),
            actor_role=RoleEnum.USER,
            actor_id=client_user.id,
        )
        assert updated.status == Appointment.STATUS_CANCELLED


# -----------------------------------------------------------------------------
# Upcoming
# -----------------------------------------------------------------------------


class TestUpcomingAppointments:
    """Tests for upcoming_appointments_for_client and upcoming_appointments_for_lawyer."""

    def test_upcoming_for_client_includes_requested(self, appointment, client_user):
        upcoming = AppointmentService.upcoming_appointments_for_client(client_user.id)
        assert any(a.id == appointment.id for a in upcoming)

    def test_upcoming_for_lawyer_includes_requested(self, appointment, lawyer_user):
        upcoming = AppointmentService.upcoming_appointments_for_lawyer(lawyer_user.id)
        assert any(a.id == appointment.id for a in upcoming)

    def test_upcoming_excludes_cancelled(self, appointment, client_user, lawyer_user):
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CANCELLED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        upcoming = AppointmentService.upcoming_appointments_for_client(client_user.id)
        assert not any(a.id == appointment.id for a in upcoming)


# -----------------------------------------------------------------------------
# Model helpers (optional)
# -----------------------------------------------------------------------------


class TestAppointmentModelHelpers:
    """Tests for Appointment model helper methods."""

    def test_is_upcoming_true_for_future(self, appointment):
        assert appointment.is_upcoming() is True

    def test_can_be_cancelled_requested(self, appointment):
        assert appointment.status == Appointment.STATUS_REQUESTED
        assert appointment.can_be_cancelled() is True

    def test_can_be_confirmed_when_requested(self, appointment):
        assert appointment.can_be_confirmed() is True

    def test_can_be_completed_only_when_confirmed(self, appointment, lawyer_user):
        assert appointment.can_be_completed() is False
        AppointmentService.update_status(
            appointment_id=str(appointment.id),
            new_status=Appointment.STATUS_CONFIRMED,
            actor_role=RoleEnum.LAWYER,
            actor_id=lawyer_user.id,
        )
        refetched = AppointmentService.get_appointment(str(appointment.id))
        assert refetched.can_be_completed() is True
