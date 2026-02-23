from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.legal_chat_service import LegalChatService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be legal_chat_bp
legal_chat_bp = Blueprint("legal_chat_bp", __name__)


# ---------------------------------------
# Create New Chat
# ---------------------------------------
@legal_chat_bp.route("/chats", methods=["POST"])
@jwt_required()
def create_chat():
    data = request.get_json()

    if not data:
        return api_error("Invalid JSON", 400)

    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()

    if not title or not category:
        return api_error("Title and category required", 400, code="VALIDATION_ERROR")
    
    if len(title) > 255:
        return api_error("Title must be at most 255 characters", 400, code="VALIDATION_ERROR")

    valid_categories = ["family", "criminal", "civil", "corporate", "immigration", "employment", "real_estate", "other"]
    if category not in valid_categories:
        return api_error(f"Invalid category. Must be one of: {', '.join(valid_categories)}", 400, code="VALIDATION_ERROR")

    user_id = get_jwt_identity()

    try:
        chat = LegalChatService.create_chat(
            user_id=user_id,
            title=title,
            category=category
        )
        return jsonify(chat.to_dict()), 201
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get User's Chats
# ---------------------------------------
@legal_chat_bp.route("/chats", methods=["GET"])
@jwt_required()
def get_user_chats():
    user_id = get_jwt_identity()
    
    try:
        chats = LegalChatService.get_user_chats(user_id)
        return jsonify([chat.to_dict() for chat in chats])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Specific Chat
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>", methods=["GET"])
@jwt_required()
def get_chat(chat_id):
    user_id = get_jwt_identity()
    
    try:
        chat = LegalChatService.get_chat(chat_id, user_id)
        if not chat:
            return api_error("Chat not found", 404)
        return jsonify(chat.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Send Message
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>/messages", methods=["POST"])
@jwt_required()
def send_message(chat_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "content" not in data:
        return api_error("Message content required", 400, code="VALIDATION_ERROR")
    
    content = data.get("content", "").strip()
    if not content:
        return api_error("Message content cannot be empty", 400, code="VALIDATION_ERROR")

    try:
        # Verify chat belongs to user
        chat = LegalChatService.get_chat(chat_id, user_id)
        if not chat:
            return api_error("Chat not found", 404)
        
        # Add user message
        user_message = LegalChatService.add_message(chat_id, user_id, content, "user")
        
        # Generate AI response
        ai_message = LegalChatService.generate_ai_response(chat_id, user_id, content)
        
        return jsonify({
            "user_message": user_message.to_dict(),
            "ai_message": ai_message.to_dict() if ai_message else None
        })
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Chat Messages
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>/messages", methods=["GET"])
@jwt_required()
def get_chat_messages(chat_id):
    user_id = get_jwt_identity()
    
    try:
        messages = LegalChatService.get_chat_messages(chat_id, user_id)
        return jsonify([msg.to_dict() for msg in messages])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Upload Document
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>/documents", methods=["POST"])
@jwt_required()
def upload_document(chat_id):
    user_id = get_jwt_identity()
    
    # Verify chat belongs to user
    chat = LegalChatService.get_chat(chat_id, user_id)
    if not chat:
        return api_error("Chat not found", 404)
    
    if 'file' not in request.files:
        return api_error("No file provided", 400, code="VALIDATION_ERROR")
    
    file = request.files['file']
    
    try:
        document = LegalChatService.upload_document(chat_id, user_id, file)
        return jsonify(document.to_dict()), 201
    except ValueError as e:
        return api_error(str(e), 400, code="VALIDATION_ERROR")
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Chat Documents
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>/documents", methods=["GET"])
@jwt_required()
def get_chat_documents(chat_id):
    user_id = get_jwt_identity()
    
    try:
        documents = LegalChatService.get_chat_documents(chat_id, user_id)
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Request Lawyer
# ---------------------------------------
@legal_chat_bp.route("/chats/<chat_id>/request-lawyer", methods=["POST"])
@jwt_required()
def request_lawyer(chat_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "reason" not in data:
        return api_error("Reason for lawyer request required", 400, code="VALIDATION_ERROR")
    
    reason = data.get("reason", "").strip()
    if not reason:
        return api_error("Reason cannot be empty", 400, code="VALIDATION_ERROR")

    try:
        chat = LegalChatService.request_lawyer(chat_id, user_id, reason)
        if not chat:
            return api_error("Chat not found", 404)
        return jsonify(chat.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Categories
# ---------------------------------------
@legal_chat_bp.route("/categories", methods=["GET"])
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
