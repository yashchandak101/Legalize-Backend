from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.lawyer_profile_service import LawyerProfileService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error
from app.domain.enums import RoleEnum

# IMPORTANT: variable name must be lawyer_profile_bp
lawyer_profile_bp = Blueprint("lawyer_profile_bp", __name__)


# ---------------------------------------
# Get My Profile (Lawyer only)
# ---------------------------------------
@lawyer_profile_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user or user.role != RoleEnum.LAWYER.value:
        return api_error("Only lawyers can access profiles", 403, code="FORBIDDEN")
    
    profile = LawyerProfileService.get_profile_by_user_id(user_id)
    
    if not profile:
        return api_error("Profile not found", 404, code="NOT_FOUND")
    
    return jsonify(profile.to_dict()), 200


# ---------------------------------------
# Create/Update My Profile (Lawyer only)
# ---------------------------------------
@lawyer_profile_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user or user.role != RoleEnum.LAWYER.value:
        return api_error("Only lawyers can update profiles", 403, code="FORBIDDEN")
    
    try:
        # Try to update existing profile first
        profile = LawyerProfileService.update_profile(
            user_id=user_id,
            bar_number=data.get("bar_number"),
            bar_state=data.get("bar_state"),
            bio=data.get("bio"),
            specializations=data.get("specializations"),
            hourly_rate_cents=data.get("hourly_rate_cents"),
            actor_id=user_id,
            actor_role=user.role
        )
        
        # If no profile exists, create one
        if not profile:
            profile = LawyerProfileService.create_profile(
                user_id=user_id,
                bar_number=data.get("bar_number"),
                bar_state=data.get("bar_state"),
                bio=data.get("bio"),
                specializations=data.get("specializations"),
                hourly_rate_cents=data.get("hourly_rate_cents"),
                actor_id=user_id,
                actor_role=user.role
            )
        
        return jsonify(profile.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Lawyer Profile by User ID (Public)
# ---------------------------------------
@lawyer_profile_bp.route("/user/<user_id>", methods=["GET"])
@jwt_required()
def get_lawyer_profile_by_user_id(user_id):
    # Verify the user is a lawyer
    user = AuthService.get_user_by_id(user_id)
    if not user or user.role != RoleEnum.LAWYER.value:
        return api_error("Lawyer not found", 404, code="NOT_FOUND")
    
    profile = LawyerProfileService.get_profile_by_user_id(user_id)
    
    if not profile:
        return api_error("Profile not found", 404, code="NOT_FOUND")
    
    return jsonify(profile.to_dict()), 200


# ---------------------------------------
# Get Lawyer Profile by Profile ID (Public)
# ---------------------------------------
@lawyer_profile_bp.route("/<profile_id>", methods=["GET"])
@jwt_required()
def get_lawyer_profile_by_id(profile_id):
    profile = LawyerProfileService.get_profile_by_id(profile_id)
    
    if not profile:
        return api_error("Profile not found", 404, code="NOT_FOUND")
    
    return jsonify(profile.to_dict()), 200


# ---------------------------------------
# Get All Lawyer Profiles (Admin only)
# ---------------------------------------
@lawyer_profile_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_lawyer_profiles():
    user_id = get_jwt_identity()
    
    # Get user to verify admin role
    user = AuthService.get_user_by_id(user_id)
    if not user or user.role != RoleEnum.ADMIN.value:
        return api_error("Only admins can view all profiles", 403, code="FORBIDDEN")
    
    profiles = LawyerProfileService.get_all_profiles()
    
    return jsonify([profile.to_dict() for profile in profiles]), 200


# ---------------------------------------
# Delete Lawyer Profile (Admin only)
# ---------------------------------------
@lawyer_profile_bp.route("/user/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_lawyer_profile(user_id):
    actor_id = get_jwt_identity()
    
    # Get user to verify admin role
    actor = AuthService.get_user_by_id(actor_id)
    if not actor or actor.role != RoleEnum.ADMIN.value:
        return api_error("Only admins can delete profiles", 403, code="FORBIDDEN")
    
    try:
        deleted = LawyerProfileService.delete_profile(
            user_id=user_id,
            actor_id=actor_id,
            actor_role=actor.role
        )
        
        if not deleted:
            return api_error("Profile not found", 404, code="NOT_FOUND")
        
        return jsonify({"message": "Profile deleted successfully"}), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)
