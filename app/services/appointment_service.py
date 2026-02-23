from datetime import datetime
from typing import List, Optional

from ..models.appointment import Appointment
from ..repositories.appointment_repository import AppointmentRepository
from ..domain.appointment_rules import validate_status_transition, InvalidAppointmentStatusTransition
from app.domain.enums import RoleEnum


class AppointmentService:
    """Application layer for Appointment operations"""

    @staticmethod
    def create_appointment(
        client_id: str,
        lawyer_id: str,
        scheduled_at: datetime,
        duration_minutes: int = 30,
        notes: Optional[str] = None,
        meeting_link: Optional[str] = None,
    ) -> Appointment:
        """Create a new appointment request"""
        appointment = Appointment(
            client_id=client_id,
            lawyer_id=lawyer_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            notes=notes,
            meeting_link=meeting_link,
            status=Appointment.STATUS_REQUESTED,
        )
        return AppointmentRepository.create(appointment)

    @staticmethod
    def get_appointment(appointment_id: str) -> Appointment:
        """Retrieve a single appointment by ID"""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")
        return appointment

    @staticmethod
    def list_appointments_for_client(client_id: str, status: Optional[str] = None) -> List[Appointment]:
        """List all appointments for a client"""
        return AppointmentRepository.get_by_client(client_id, status=status)

    @staticmethod
    def list_appointments_for_lawyer(lawyer_id: str, status: Optional[str] = None) -> List[Appointment]:
        """List all appointments for a lawyer"""
        return AppointmentRepository.get_by_lawyer(lawyer_id, status=status)

    @staticmethod
    def update_status(
        appointment_id: str,
        new_status: str,
        actor_role: RoleEnum,
        actor_id: str
    ) -> Appointment:
        """
        Update appointment status with validation:
        - Clients can only cancel their REQUESTED or CONFIRMED appointments
        - Lawyers can confirm, cancel, or complete appointments
        """
        appointment = AppointmentService.get_appointment(appointment_id)

        # Validate status transition
        try:
            validate_status_transition(appointment.status, new_status)
        except InvalidAppointmentStatusTransition as e:
            raise ValueError(str(e))

        # Role-based enforcement
        if actor_role == RoleEnum.USER:
            if new_status != Appointment.STATUS_CANCELLED:
                raise PermissionError("Clients can only cancel appointments")
            if appointment.client_id != actor_id:
                raise PermissionError("Client cannot modify another client's appointment")
        elif actor_role == RoleEnum.LAWYER:
            if new_status not in [
                Appointment.STATUS_CONFIRMED,
                Appointment.STATUS_CANCELLED,
                Appointment.STATUS_COMPLETED,
            ]:
                raise PermissionError("Lawyers can only confirm, complete, or cancel appointments")
            if appointment.lawyer_id != actor_id:
                raise PermissionError("Lawyer cannot modify another lawyer's appointment")
        else:
            raise PermissionError("Invalid role for appointment update")

        return AppointmentRepository.update_status(appointment, new_status)

    @staticmethod
    def cancel_appointment(
        appointment_id: str,
        actor_role: RoleEnum,
        actor_id: str
    ) -> Appointment:
        """Convenience method for cancelling an appointment"""
        return AppointmentService.update_status(
            appointment_id,
            Appointment.STATUS_CANCELLED,
            actor_role,
            actor_id
        )

    @staticmethod
    def upcoming_appointments_for_lawyer(lawyer_id: str) -> List[Appointment]:
        """Get all upcoming appointments for a lawyer"""
        return AppointmentRepository.upcoming_for_lawyer(lawyer_id)

    @staticmethod
    def upcoming_appointments_for_client(client_id: str) -> List[Appointment]:
        """Get all upcoming appointments for a client"""
        return AppointmentRepository.upcoming_for_client(client_id)