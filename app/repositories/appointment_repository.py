from typing import List, Optional
from datetime import datetime, timezone

from ..core.extensions import db
from ..models.appointment import Appointment


class AppointmentRepository:
    """Database abstraction layer for Appointment model."""

    @staticmethod
    def create(appointment: Appointment) -> Appointment:
        """Add a new appointment to the DB."""
        try:
            db.session.add(appointment)
            db.session.commit()
            db.session.refresh(appointment)
            return appointment
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_by_id(appointment_id: str) -> Optional[Appointment]:
        """Fetch an appointment by its ID."""
        session = db.session() if callable(db.session) else db.session
        return session.get(Appointment, appointment_id)

    @staticmethod
    def get_by_client(client_id: str, status: Optional[str] = None) -> List[Appointment]:
        """Fetch appointments for a client, optionally filtered by status."""
        query = Appointment.query.filter(Appointment.client_id == client_id)
        if status:
            query = query.filter(Appointment.status == status)
        return query.order_by(Appointment.scheduled_at.desc()).all()

    @staticmethod
    def get_by_lawyer(lawyer_id: str, status: Optional[str] = None) -> List[Appointment]:
        """Fetch appointments for a lawyer, optionally filtered by status."""
        query = Appointment.query.filter(Appointment.lawyer_id == lawyer_id)
        if status:
            query = query.filter(Appointment.status == status)
        return query.order_by(Appointment.scheduled_at.desc()).all()

    @staticmethod
    def update_status(appointment: Appointment, new_status: str) -> Appointment:
        """Update the status of an appointment."""
        if new_status not in Appointment.STATUS_CHOICES:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {Appointment.STATUS_CHOICES}")
        try:
            appointment.status = new_status
            db.session.commit()
            db.session.refresh(appointment)
            return appointment
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete(appointment: Appointment) -> None:
        """Delete an appointment."""
        try:
            db.session.delete(appointment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def upcoming_for_lawyer(lawyer_id: str) -> List[Appointment]:
        """Fetch upcoming appointments for a lawyer."""
        return (
            Appointment.query
            .filter(
                Appointment.lawyer_id == lawyer_id,
                Appointment.scheduled_at > datetime.now(timezone.utc),
                Appointment.status.in_([Appointment.STATUS_REQUESTED, Appointment.STATUS_CONFIRMED])
            )
            .order_by(Appointment.scheduled_at.asc())
            .all()
        )

    @staticmethod
    def upcoming_for_client(client_id: str) -> List[Appointment]:
        """Fetch upcoming appointments for a client."""
        return (
            Appointment.query
            .filter(
                Appointment.client_id == client_id,
                Appointment.scheduled_at > datetime.now(timezone.utc),
                Appointment.status.in_([Appointment.STATUS_REQUESTED, Appointment.STATUS_CONFIRMED])
            )
            .order_by(Appointment.scheduled_at.asc())
            .all()
        )