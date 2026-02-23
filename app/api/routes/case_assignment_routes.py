from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.case_assignment_service import CaseAssignmentService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error
from app.domain.enums import RoleEnum

# IMPORTANT: variable name must be case_assignment_bp
case_assignment_bp = Blueprint("case_assignment_bp", __name__)


# ---------------------------------------
# Assign Case to Lawyer (Admin only)
# ---------------------------------------
@case_assignment_bp.route("/cases/<case_id>/assign", methods=["POST"])
@jwt_required()
def assign_case(case_id):
    actor_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    lawyer_id = data.get("lawyer_id")
    if not lawyer_id:
        return api_error("Lawyer ID required", 400, code="VALIDATION_ERROR")
    
    # Get actor to verify admin role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor or actor.role != RoleEnum.ADMIN.value:
        return api_error("Only admins can assign cases", 403, code="FORBIDDEN")
    
    try:
        assignment = CaseAssignmentService.assign_case(
            case_id=case_id,
            lawyer_id=lawyer_id,
            assigned_by=actor_id,
            actor_role=actor.role
        )
        return jsonify(assignment.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Unassign Case (Admin only)
# ---------------------------------------
@case_assignment_bp.route("/cases/<case_id>/unassign", methods=["POST"])
@jwt_required()
def unassign_case(case_id):
    actor_id = get_jwt_identity()
    
    # Get actor to verify admin role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor or actor.role != RoleEnum.ADMIN.value:
        return api_error("Only admins can unassign cases", 403, code="FORBIDDEN")
    
    try:
        success = CaseAssignmentService.unassign_case(
            case_id=case_id,
            assigned_by=actor_id,
            actor_role=actor.role
        )
        
        if not success:
            return api_error("No active assignment found", 404, code="NOT_FOUND")
        
        return jsonify({"message": "Case unassigned successfully"}), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Case Assignments (History)
# ---------------------------------------
@case_assignment_bp.route("/cases/<case_id>/assignments", methods=["GET"])
@jwt_required()
def get_case_assignments(case_id):
    actor_id = get_jwt_identity()
    
    # Get actor to verify role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    # Check if user can access the case
    can_access = CaseAssignmentService.can_user_access_case(
        user_id=actor_id,
        case_id=case_id,
        user_role=actor.role
    )
    
    if not can_access:
        return api_error("Unauthorized", 403, code="FORBIDDEN")
    
    try:
        assignments = CaseAssignmentService.get_case_assignments(case_id)
        return jsonify([assignment.to_dict() for assignment in assignments]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Active Assignment for Case
# ---------------------------------------
@case_assignment_bp.route("/cases/<case_id>/assignment", methods=["GET"])
@jwt_required()
def get_active_assignment(case_id):
    actor_id = get_jwt_identity()
    
    # Get actor to verify role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    # Check if user can access the case
    can_access = CaseAssignmentService.can_user_access_case(
        user_id=actor_id,
        case_id=case_id,
        user_role=actor.role
    )
    
    if not can_access:
        return api_error("Unauthorized", 403, code="FORBIDDEN")
    
    try:
        assignment = CaseAssignmentService.get_active_assignment(case_id)
        
        if not assignment:
            return api_error("No active assignment found", 404, code="NOT_FOUND")
        
        return jsonify(assignment.to_dict()), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Lawyer's Assignments
# ---------------------------------------
@case_assignment_bp.route("/lawyers/<lawyer_id>/assignments", methods=["GET"])
@jwt_required()
def get_lawyer_assignments(lawyer_id):
    actor_id = get_jwt_identity()
    
    # Get actor to verify role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    # Only the lawyer themselves or admins can view assignments
    if actor.role != RoleEnum.ADMIN.value and actor_id != lawyer_id:
        return api_error("Unauthorized", 403, code="FORBIDDEN")
    
    # Check if lawyer_id is actually a lawyer
    lawyer = AuthService.get_user_by_id(lawyer_id)
    if not lawyer or lawyer.role != RoleEnum.LAWYER.value:
        return api_error("Lawyer not found", 404, code="NOT_FOUND")
    
    try:
        active_only = request.args.get("active_only", "false").lower() == "true"
        assignments = CaseAssignmentService.get_lawyer_assignments(
            lawyer_id=lawyer_id,
            active_only=active_only
        )
        return jsonify([assignment.to_dict() for assignment in assignments]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get My Assignments (Lawyer only)
# ---------------------------------------
@case_assignment_bp.route("/my-assignments", methods=["GET"])
@jwt_required()
def get_my_assignments():
    actor_id = get_jwt_identity()
    
    # Get actor to verify lawyer role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor or actor.role != RoleEnum.LAWYER.value:
        return api_error("Only lawyers can view their assignments", 403, code="FORBIDDEN")
    
    try:
        active_only = request.args.get("active_only", "false").lower() == "true"
        assignments = CaseAssignmentService.get_lawyer_assignments(
            lawyer_id=actor_id,
            active_only=active_only
        )
        return jsonify([assignment.to_dict() for assignment in assignments]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)
