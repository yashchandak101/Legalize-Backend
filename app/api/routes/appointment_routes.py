# app/api/routes/appointment_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from dateutil.parser import parse as parse_datetime

from app.domain.enums import RoleEnum
from app.domain.appointment_rules import InvalidAppointmentStatusTransition
from app.services.appointment_service import AppointmentService
from app.core.extensions import db

appointment_bp = Blueprint("appointment_bp", __name__)


# -------------------------------
# Simple Role Check Decorator
# -------------------------------
def role_required(role: RoleEnum):
    """Ensure the user has the required role (from JWT payload)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            payload = get_jwt()
            user_role = payload.get("role", RoleEnum.USER.value)
            if user_role != role.value:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# -------------------------------
# CREATE APPOINTMENT (Client Only)
# -------------------------------
@appointment_bp.route("/", methods=["POST"])
@jwt_required()
@role_required(RoleEnum.USER)
def create_appointment():
    data = request.json
    client_id = get_jwt_identity()

    lawyer_id = data.get("lawyer_id")
    if not lawyer_id:
        return jsonify({"error": "lawyer_id is required"}), 400

    scheduled_at_str = data.get("scheduled_at")
    if not scheduled_at_str:
        return jsonify({"error": "scheduled_at is required"}), 400

    try:
        scheduled_at = parse_datetime(scheduled_at_str)
    except Exception:
        return jsonify({"error": "scheduled_at must be valid ISO datetime"}), 400

    duration_minutes = data.get("duration_minutes", 30)
    notes = data.get("notes")
    meeting_link = data.get("meeting_link")

    try:
        appointment = AppointmentService.create_appointment(
            client_id=client_id,
            lawyer_id=lawyer_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            notes=notes,
            meeting_link=meeting_link,
        )
        return jsonify({"appointment_id": str(appointment.id), "status": appointment.status}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# -------------------------------
# LIST APPOINTMENTS (Client)
# -------------------------------
@appointment_bp.route("/client", methods=["GET"])
@jwt_required()
@role_required(RoleEnum.USER)
def list_client_appointments():
    client_id = get_jwt_identity()
    status = request.args.get("status")
    appointments = AppointmentService.list_appointments_for_client(client_id, status=status)
    return jsonify([
        {
            "id": str(appt.id),
            "lawyer_id": appt.lawyer_id,
            "scheduled_at": appt.scheduled_at.isoformat(),
            "duration_minutes": appt.duration_minutes,
            "status": appt.status
        } for appt in appointments
    ]), 200


# -------------------------------
# LIST APPOINTMENTS (Lawyer)
# -------------------------------
@appointment_bp.route("/lawyer", methods=["GET"])
@jwt_required()
@role_required(RoleEnum.LAWYER)
def list_lawyer_appointments():
    lawyer_id = get_jwt_identity()
    status = request.args.get("status")
    appointments = AppointmentService.list_appointments_for_lawyer(lawyer_id, status=status)
    return jsonify([
        {
            "id": str(appt.id),
            "client_id": appt.client_id,
            "scheduled_at": appt.scheduled_at.isoformat(),
            "duration_minutes": appt.duration_minutes,
            "status": appt.status
        } for appt in appointments
    ]), 200


# -------------------------------
# GET SINGLE APPOINTMENT
# -------------------------------
@appointment_bp.route("/<string:appointment_id>", methods=["GET"])
@jwt_required()
def get_appointment(appointment_id: str):
    user_id = get_jwt_identity()
    try:
        appt = AppointmentService.get_appointment(appointment_id)
        if user_id not in [appt.client_id, appt.lawyer_id]:
            return jsonify({"error": "Forbidden"}), 403

        return jsonify({
            "id": str(appt.id),
            "client_id": appt.client_id,
            "lawyer_id": appt.lawyer_id,
            "scheduled_at": appt.scheduled_at.isoformat(),
            "duration_minutes": appt.duration_minutes,
            "status": appt.status,
            "notes": appt.notes,
            "meeting_link": appt.meeting_link
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# -------------------------------
# UPDATE STATUS (Client or Lawyer)
# -------------------------------
@appointment_bp.route("/<string:appointment_id>/status", methods=["PUT"])
@jwt_required()
def update_appointment_status(appointment_id: str):
    data = request.json
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status is required"}), 400

    actor_id = get_jwt_identity()
    payload = get_jwt()
    role = payload.get("role", RoleEnum.USER.value)

    try:
        updated = AppointmentService.update_status(
            appointment_id=appointment_id,
            new_status=new_status,
            actor_role=RoleEnum(role),
            actor_id=actor_id
        )
        return jsonify({"id": str(updated.id), "status": updated.status}), 200
    except InvalidAppointmentStatusTransition as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400