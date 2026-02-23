from datetime import datetime, timezone
from typing import Literal

from ..core.extensions import db
from .base import BaseModel


class Appointment(BaseModel):
    """
    Appointment between a client (User with role='user')
    and a lawyer (User with role='lawyer').

    Status flow:
    REQUESTED -> CONFIRMED -> COMPLETED
    REQUESTED -> CANCELLED
    CONFIRMED -> CANCELLED
    """

    __tablename__ = "appointments"

    # --- Status Constants ---
    STATUS_REQUESTED = "REQUESTED"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        STATUS_REQUESTED,
        STATUS_CONFIRMED,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
    ]

    # --- Foreign Keys ---
    client_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lawyer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Appointment Details ---
    scheduled_at = db.Column(
        db.DateTime,
        nullable=False,
        index=True,
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False,
        default=30,
    )

    meeting_link = db.Column(
        db.String(500),
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_REQUESTED,
        index=True,
    )

    # --- Relationships ---
    client = db.relationship(
        "User",
        foreign_keys="[Appointment.client_id]",
        back_populates="appointments_as_client",
    )

    lawyer = db.relationship(
        "User",
        foreign_keys="[Appointment.lawyer_id]",
        back_populates="appointments_as_lawyer",
    )

    # --- Constraints ---
    __table_args__ = (
        db.CheckConstraint(
            f"status IN {tuple(STATUS_CHOICES)}",
            name="check_appointment_status",
        ),
    )

    # --- Business Helpers ---
    def is_upcoming(self) -> bool:
        """Return True if appointment is in the future."""
        now = datetime.now(timezone.utc)
        at = self.scheduled_at if self.scheduled_at.tzinfo else self.scheduled_at.replace(tzinfo=timezone.utc)
        return at > now

    def can_be_cancelled(self) -> bool:
        """Return True if appointment can be cancelled."""
        return self.status in [self.STATUS_REQUESTED, self.STATUS_CONFIRMED]

    def can_be_confirmed(self) -> bool:
        """Return True if appointment can be confirmed."""
        return self.status == self.STATUS_REQUESTED

    def can_be_completed(self) -> bool:
        """Return True if appointment can be marked completed."""
        return self.status == self.STATUS_CONFIRMED