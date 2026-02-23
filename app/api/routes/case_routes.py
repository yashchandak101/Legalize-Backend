from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error
from app.domain.case_rules import InvalidCaseStatusTransition
from app.domain.enums import RoleEnum

# IMPORTANT: variable name must be case_bp
case_bp = Blueprint("case_bp", __name__)


# ---------------------------------------
# Create Case
# ---------------------------------------
@case_bp.route("/", methods=["POST"])
@jwt_required()
def create_case():
    data = request.get_json()

    if not data:
        return api_error("Invalid JSON", 400)

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title or not description:
        return api_error("Title and description required", 400, code="VALIDATION_ERROR")
    if len(title) > 255:
        return api_error("Title must be at most 255 characters", 400, code="VALIDATION_ERROR")

    user_id = get_jwt_identity()

    try:
        case = CaseService.create_case(
            user_id=user_id,
            title=title,
            description=description,
        )
    except Exception as e:
        return api_error(str(e), 400)
    return jsonify(case.to_dict()), 201


# ---------------------------------------
# List Cases (Role-based)
# ---------------------------------------
@case_bp.route("/", methods=["GET"])
@jwt_required()
def list_cases():
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    # Get query parameters for filtering
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('assigned_lawyer_id'):
        filters['assigned_lawyer_id'] = request.args.get('assigned_lawyer_id')
    
    try:
        cases = CaseService.get_cases_for_user(
            user_id=user_id,
            user_role=user.role,
            filters=filters
        )
        return jsonify([c.to_dict() for c in cases]), 200
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Single Case
# ---------------------------------------
@case_bp.route("/<case_id>", methods=["GET"])
@jwt_required()
def get_case(case_id):
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    case = CaseService.get_case_by_id(case_id)

    if not case:
        return api_error("Case not found", 404, code="NOT_FOUND")

    # Check authorization using CaseAssignmentService
    from app.services.case_assignment_service import CaseAssignmentService
    if not CaseAssignmentService.can_user_access_case(user_id, case_id, user.role):
        return api_error("Unauthorized", 403, code="FORBIDDEN")

    return jsonify(case.to_dict()), 200


# ---------------------------------------
# Update Case
# ---------------------------------------
@case_bp.route("/<case_id>", methods=["PUT"])
@jwt_required()
def update_case(case_id):
    data = request.get_json()

    if not data:
        return api_error("Invalid JSON", 400)

    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    case = CaseService.get_case_by_id(case_id)

    if not case:
        return api_error("Case not found", 404, code="NOT_FOUND")

    try:
        updated_case = CaseService.update_case(
            case_id=case_id,
            title=data.get("title"),
            description=data.get("description"),
            status=data.get("status"),
            actor_id=user_id,
            actor_role=user.role
        )
    except InvalidCaseStatusTransition as e:
        return api_error(str(e), 400, code="INVALID_STATUS_TRANSITION")
    except ValueError as e:
        return api_error(str(e), 403, code="FORBIDDEN")
    except Exception as e:
        return api_error(str(e), 400)

    if not updated_case:
        return api_error("Update failed", 400)

    return jsonify(updated_case.to_dict()), 200


# ---------------------------------------
# Delete Case
# ---------------------------------------
@case_bp.route("/<case_id>", methods=["DELETE"])
@jwt_required()
def delete_case(case_id):
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    case = CaseService.get_case_by_id(case_id)

    if not case:
        return api_error("Case not found", 404, code="NOT_FOUND")

    try:
        deleted = CaseService.delete_case(
            case_id=case_id,
            actor_id=user_id,
            actor_role=user.role
        )
    except ValueError as e:
        return api_error(str(e), 403, code="FORBIDDEN")
    except Exception as e:
        return api_error(str(e), 400)

    if not deleted:
        return api_error("Delete failed", 400)

    return jsonify({"message": "Case deleted successfully"}), 200


# ---------------------------------------
# Get All Cases (Admin only)
# ---------------------------------------
@case_bp.route("/admin/all", methods=["GET"])
@jwt_required()
def get_all_cases():
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    
    if not user or user.role != RoleEnum.ADMIN.value:
        return api_error("Only admins can view all cases", 403, code="FORBIDDEN")
    
    try:
        cases = CaseService.get_all_cases()
        return jsonify([c.to_dict() for c in cases]), 200
    except Exception as e:
        return api_error(str(e), 400)