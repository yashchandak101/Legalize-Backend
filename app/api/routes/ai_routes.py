from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.case_ai_suggestion_service import CaseAISuggestionService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be ai_bp
ai_bp = Blueprint("ai_bp", __name__)


# ---------------------------------------
# Create Case Suggestions
# ---------------------------------------
@ai_bp.route("/cases/<case_id>/suggestions", methods=["POST"])
@jwt_required()
def create_case_suggestions(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    async_processing = data.get("async_processing", False)
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        suggestion = CaseAISuggestionService.create_case_suggestion(
            case_id=case_id,
            user_id=user_id,
            actor_role=user.role,
            async_processing=async_processing
        )
        
        return jsonify(suggestion.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Case Suggestions
# ---------------------------------------
@ai_bp.route("/cases/<case_id>/suggestions", methods=["GET"])
@jwt_required()
def get_case_suggestions(case_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        suggestions = CaseAISuggestionService.get_case_suggestions(
            case_id=case_id,
            user_id=user_id,
            user_role=user.role
        )
        return jsonify([suggestion.to_dict() for suggestion in suggestions]), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get User Suggestions
# ---------------------------------------
@ai_bp.route("/suggestions", methods=["GET"])
@jwt_required()
def get_user_suggestions():
    user_id = get_jwt_identity()
    
    try:
        suggestions = CaseAISuggestionService.get_user_suggestions(user_id)
        return jsonify([suggestion.to_dict() for suggestion in suggestions]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Single Suggestion
# ---------------------------------------
@ai_bp.route("/suggestions/<suggestion_id>", methods=["GET"])
@jwt_required()
def get_suggestion(suggestion_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        suggestion = CaseAISuggestionService.get_suggestion_by_id(
            suggestion_id=suggestion_id,
            user_id=user_id,
            user_role=user.role
        )
        
        if not suggestion:
            return api_error("Suggestion not found", 404, code="NOT_FOUND")
        
        return jsonify(suggestion.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Create Document Analysis
# ---------------------------------------
@ai_bp.route("/documents/<document_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_document(document_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    async_processing = data.get("async_processing", False)
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        suggestion = CaseAISuggestionService.create_document_suggestion(
            document_id=document_id,
            user_id=user_id,
            actor_role=user.role,
            async_processing=async_processing
        )
        
        return jsonify(suggestion.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Document Analyses
# ---------------------------------------
@ai_bp.route("/documents/<document_id>/analyses", methods=["GET"])
@jwt_required()
def get_document_analyses(document_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        # Get document to find case_id
        from app.models.case_document import CaseDocument
        document = CaseDocument.query.get(document_id)
        if not document:
            return api_error("Document not found", 404, code="NOT_FOUND")
        
        # Check if user can access the case
        from app.services.case_assignment_service import CaseAssignmentService
        if not CaseAssignmentService.can_user_access_case(user_id, document.case_id, user.role):
            return api_error("Unauthorized to access this document", 403, code="FORBIDDEN")
        
        # Get suggestions for the case (document analyses)
        suggestions = CaseAISuggestionService.get_case_suggestions(
            case_id=document.case_id,
            user_id=user_id,
            user_role=user.role
        )
        
        # Filter for document analyses
        document_analyses = [
            s for s in suggestions 
            if s.suggestion_type == "document_analysis" and 
            s.request_data and s.request_data.get("document_id") == document_id
        ]
        
        return jsonify([s.to_dict() for s in document_analyses]), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# AI Service Status
# ---------------------------------------
@ai_bp.route("/status", methods=["GET"])
@jwt_required()
def get_ai_status():
    """Get AI service status and configuration."""
    user_id = get_jwt_identity()
    
    try:
        from app.services.ai_service import AIService
        ai_service = AIService()
        
        status = {
            "service_available": True,
            "default_provider": ai_service.default_provider,
            "providers": {
                "openai": bool(ai_service.openai_api_key),
                "anthropic": bool(ai_service.anthropic_api_key),
                "mock": True  # Always available as fallback
            },
            "features": {
                "case_suggestions": True,
                "document_analysis": True,
                "async_processing": True
            },
            "rate_limits": {
                "case_suggestions_per_day": 5,
                "document_analyses_per_day": 3
            }
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)