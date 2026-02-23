from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.legal_case_service import LegalCaseService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be legal_case_bp
legal_case_bp = Blueprint("legal_case_bp", __name__)


# ---------------------------------------
# Create New Case
# ---------------------------------------
@legal_case_bp.route("/cases", methods=["POST"])
@jwt_required()
def create_case():
    data = request.get_json()

    if not data:
        return api_error("Invalid JSON", 400)

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "").strip()
    urgency = (data.get("urgency") or "medium").strip()

    if not title or not description or not category:
        return api_error("Title, description, and category required", 400, code="VALIDATION_ERROR")
    
    if len(title) > 255:
        return api_error("Title must be at most 255 characters", 400, code="VALIDATION_ERROR")

    valid_categories = ["family", "criminal", "civil", "corporate", "immigration", "employment", "real_estate", "other"]
    if category not in valid_categories:
        return api_error(f"Invalid category. Must be one of: {', '.join(valid_categories)}", 400, code="VALIDATION_ERROR")

    valid_urgency = ["low", "medium", "high", "urgent"]
    if urgency not in valid_urgency:
        return api_error(f"Invalid urgency. Must be one of: {', '.join(valid_urgency)}", 400, code="VALIDATION_ERROR")

    user_id = get_jwt_identity()

    try:
        case = LegalCaseService.create_case(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            urgency=urgency
        )
        return jsonify(case.to_dict()), 201
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get User's Cases
# ---------------------------------------
@legal_case_bp.route("/cases", methods=["GET"])
@jwt_required()
def get_user_cases():
    user_id = get_jwt_identity()
    include_shared = request.args.get("include_shared", "false").lower() == "true"
    
    try:
        cases = LegalCaseService.get_user_cases(user_id, include_shared)
        return jsonify([case.to_dict(include_shared=include_shared) for case in cases])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Specific Case
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    user_id = None
    share_token = request.args.get("share_token")
    
    # Try to get user ID from JWT if available
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except:
        pass
    
    try:
        case = LegalCaseService.get_case(case_id, user_id, share_token)
        if not case:
            return api_error("Case not found", 404)
        return jsonify(case.to_dict(include_shared=True))
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Send Message
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/messages", methods=["POST"])
@jwt_required()
def send_message(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "content" not in data:
        return api_error("Message content required", 400, code="VALIDATION_ERROR")
    
    content = data.get("content", "").strip()
    if not content:
        return api_error("Message content cannot be empty", 400, code="VALIDATION_ERROR")

    try:
        # Verify user has access to case
        case = LegalCaseService.get_case(case_id, user_id)
        if not case:
            return api_error("Case not found", 404)
        
        # Add user message
        user_message = LegalCaseService.add_message(case_id, user_id, content, "user")
        
        # Generate AI response
        ai_message = LegalCaseService.generate_ai_response(case_id, user_id, content)
        
        return jsonify({
            "user_message": user_message.to_dict(),
            "ai_message": ai_message.to_dict() if ai_message else None
        })
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Case Messages
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/messages", methods=["GET"])
@jwt_required()
def get_case_messages(case_id):
    user_id = get_jwt_identity()
    
    try:
        messages = LegalCaseService.get_case_messages(case_id, user_id)
        return jsonify([msg.to_dict() for msg in messages])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Upload Document
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/documents", methods=["POST"])
@jwt_required()
def upload_document(case_id):
    user_id = get_jwt_identity()
    
    # Verify user has access to case
    case = LegalCaseService.get_case(case_id, user_id)
    if not case:
        return api_error("Case not found", 404)
    
    if 'file' not in request.files:
        return api_error("No file provided", 400, code="VALIDATION_ERROR")
    
    file = request.files['file']
    
    try:
        document = LegalCaseService.upload_document(case_id, user_id, file)
        return jsonify(document.to_dict()), 201
    except ValueError as e:
        return api_error(str(e), 400, code="VALIDATION_ERROR")
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Case Documents
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/documents", methods=["GET"])
@jwt_required()
def get_case_documents(case_id):
    user_id = get_jwt_identity()
    
    try:
        documents = LegalCaseService.get_case_documents(case_id, user_id)
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Request Lawyer
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/request-lawyer", methods=["POST"])
@jwt_required()
def request_lawyer(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "reason" not in data:
        return api_error("Reason for lawyer request required", 400, code="VALIDATION_ERROR")
    
    reason = data.get("reason", "").strip()
    if not reason:
        return api_error("Reason cannot be empty", 400, code="VALIDATION_ERROR")

    try:
        case = LegalCaseService.request_lawyer(case_id, user_id, reason)
        if not case:
            return api_error("Case not found", 404)
        return jsonify(case.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Share Case
# ---------------------------------------
@legal_case_bp.route("/cases/<case_id>/share", methods=["POST"])
@jwt_required()
def share_case(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    shared_with_user_id = data.get("shared_with_user_id")
    permission_level = data.get("permission_level", "view")
    message = data.get("message", "")
    allow_public = data.get("allow_public", False)
    
    if not shared_with_user_id and not allow_public:
        return api_error("Either shared_with_user_id or allow_public required", 400, code="VALIDATION_ERROR")

    valid_permissions = ["view", "comment", "edit"]
    if permission_level not in valid_permissions:
        return api_error(f"Invalid permission. Must be one of: {', '.join(valid_permissions)}", 400, code="VALIDATION_ERROR")

    try:
        case = LegalCaseService.share_case(
            case_id, user_id, shared_with_user_id, 
            permission_level, message, allow_public
        )
        if not case:
            return api_error("Case not found", 404)
        return jsonify(case.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Shared Cases
# ---------------------------------------
@legal_case_bp.route("/shared-cases", methods=["GET"])
@jwt_required()
def get_shared_cases():
    user_id = get_jwt_identity()
    
    try:
        cases = LegalCaseService.get_shared_cases(user_id)
        return jsonify([case.to_dict() for case in cases])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Categories
# ---------------------------------------
@legal_case_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = [
        {"value": "family", "label": "Family Law"},
        {"value": "criminal", "label": "Criminal Law"},
        {"value": "civil", "label": "Civil Law"},
        {"value": "corporate", "label": "Corporate Law"},
        {"value": "immigration", "label": "Immigration Law"},
        {"value": "employment", "label": "Employment Law"},
        {"value": "real_estate", "label": "Real Estate Law"},
        {"value": "other", "label": "Other"}
    ]
    return jsonify(categories)
