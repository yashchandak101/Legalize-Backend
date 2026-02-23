from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.case_comment_service import CaseCommentService
from app.services.auth_service import AuthService
from app.repositories.case_comment_repository import CaseCommentRepository
from app.core.api_errors import api_error

# IMPORTANT: variable name must be case_comment_bp
case_comment_bp = Blueprint("case_comment_bp", __name__)


# ---------------------------------------
# Create Comment
# ---------------------------------------
@case_comment_bp.route("/cases/<case_id>/comments", methods=["POST"])
@jwt_required()
def create_comment(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    body = data.get("body", "").strip()
    is_internal = data.get("is_internal", False)
    
    if not body:
        return api_error("Comment body required", 400, code="VALIDATION_ERROR")
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        comment = CaseCommentService.create_comment(
            case_id=case_id,
            user_id=user_id,
            body=body,
            is_internal=is_internal,
            actor_role=user.role
        )
        return jsonify(comment.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Case Comments
# ---------------------------------------
@case_comment_bp.route("/cases/<case_id>/comments", methods=["GET"])
@jwt_required()
def get_case_comments(case_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        comments = CaseCommentService.get_case_comments(
            case_id=case_id,
            user_id=user_id,
            user_role=user.role
        )
        return jsonify([comment.to_dict() for comment in comments]), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Update Comment
# ---------------------------------------
@case_comment_bp.route("/comments/<comment_id>", methods=["PUT"])
@jwt_required()
def update_comment(comment_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        comment = CaseCommentService.update_comment(
            comment_id=comment_id,
            user_id=user_id,
            body=data.get("body"),
            is_internal=data.get("is_internal"),
            actor_role=user.role
        )
        
        if not comment:
            return api_error("Comment not found", 404, code="NOT_FOUND")
        
        return jsonify(comment.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Delete Comment
# ---------------------------------------
@case_comment_bp.route("/comments/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        deleted = CaseCommentService.delete_comment(
            comment_id=comment_id,
            user_id=user_id,
            actor_role=user.role
        )
        
        if not deleted:
            return api_error("Comment not found", 404, code="NOT_FOUND")
        
        return jsonify({"message": "Comment deleted successfully"}), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Single Comment
# ---------------------------------------
@case_comment_bp.route("/comments/<comment_id>", methods=["GET"])
@jwt_required()
def get_comment(comment_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        if not CaseCommentService.can_user_view_comment(
            comment_id=comment_id,
            user_id=user_id,
            user_role=user.role
        ):
            return api_error("Unauthorized", 403, code="FORBIDDEN")
        
        comment = CaseCommentRepository.get_by_id(comment_id)
        if not comment:
            return api_error("Comment not found", 404, code="NOT_FOUND")
        
        return jsonify(comment.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)
