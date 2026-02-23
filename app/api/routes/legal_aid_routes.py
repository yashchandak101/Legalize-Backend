from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.legal_aid_service import LegalAidService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be legal_aid_bp
legal_aid_bp = Blueprint("legal_aid_bp", __name__)


# ---------------------------------------
# Test Database Connection
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/test-db", methods=["GET"])
@jwt_required()
def test_database():
    """Test database connection and basic operations."""
    try:
        from app.core.extensions import db
        from app.models.legal_aid_conversation import LegalAidConversation
        from app.models.legal_aid_message import LegalAidMessage
        
        user_id = get_jwt_identity()
        
        # Test database connection
        result = db.session.execute("SELECT 1").fetchone()
        print("Database connection test:", result)
        
        # Test model creation
        test_conv = LegalAidConversation(
            user_id=user_id,
            title="Test",
            category="family",
            description="Test",
            share_token="test_token"
        )
        print("Model creation successful")
        
        return jsonify({
            "status": "success",
            "database": "connected",
            "models": "working",
            "user_id": user_id
        })
        
    except Exception as e:
        print("Database test error:", str(e))
        import traceback
        traceback.print_exc()
        return api_error(f"Database test failed: {str(e)}", 500)


# ---------------------------------------
# Create New Conversation
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations", methods=["POST"])
@jwt_required()
def create_conversation():
    data = request.get_json()
    print("Received data:", data)  # Debug line

    if not data:
        return api_error("Invalid JSON", 400)

    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    
    print("Parsed data - title:", title, "category:", category, "description:", description)  # Debug line

    if not title or not category:
        print("Validation failed - missing title or category")  # Debug line
        return api_error("Title and category required", 400, code="VALIDATION_ERROR")
    
    if len(title) > 255:
        print("Title too long:", len(title))  # Debug line
        return api_error("Title must be at most 255 characters", 400, code="VALIDATION_ERROR")

    valid_categories = ["family", "criminal", "civil", "corporate", "immigration", "employment", "real_estate", "other"]
    if category not in valid_categories:
        print("Invalid category:", category)  # Debug line
        return api_error(f"Invalid category. Must be one of: {', '.join(valid_categories)}", 400, code="VALIDATION_ERROR")

    user_id = get_jwt_identity()
    print("User ID:", user_id)  # Debug line

    try:
        print("About to call LegalAidService.create_conversation...")
        
        # Test basic database connection first
        from app.core.extensions import db
        from app.models.legal_aid_conversation import LegalAidConversation
        print("Database and model imports successful")
        
        try:
            conversation = LegalAidService.create_conversation(
                user_id=user_id,
                title=title,
                category=category,
                description=description
            )
            print("Conversation created successfully:", conversation.id if conversation else "None")
        except Exception as service_error:
            print(f"Service failed, trying direct creation: {service_error}")
            
            # Fallback: Create conversation directly
            import secrets
            conversation = LegalAidConversation(
                user_id=user_id,
                title=title,
                category=category,
                description=description,
                share_token=secrets.token_urlsafe(32)
            )
            db.session.add(conversation)
            db.session.commit()
            print("Direct conversation created:", conversation.id)
        
        print("About to serialize conversation...")
        conversation_dict = conversation.to_dict()
        print("Conversation serialized successfully")
        
        return jsonify(conversation_dict), 201
    except Exception as e:
        print("Error in create_conversation:", str(e))
        import traceback
        traceback.print_exc()
        return api_error(str(e), 400)


# ---------------------------------------
# Get User's Conversations
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations", methods=["GET"])
@jwt_required()
def get_user_conversations():
    user_id = get_jwt_identity()
    
    try:
        conversations = LegalAidService.get_user_conversations(user_id)
        return jsonify([conv.to_dict() for conv in conversations])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Specific Conversation
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
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
        conversation = LegalAidService.get_conversation(conversation_id, user_id, share_token)
        if not conversation:
            return api_error("Conversation not found", 404)
        return jsonify(conversation.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Send Message
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations/<conversation_id>/messages", methods=["POST"])
@jwt_required()
def send_message(conversation_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or "content" not in data:
        return api_error("Message content required", 400, code="VALIDATION_ERROR")
    
    content = data.get("content", "").strip()
    if not content:
        return api_error("Message content cannot be empty", 400, code="VALIDATION_ERROR")

    try:
        # Verify user has access to conversation
        conversation = LegalAidService.get_conversation(conversation_id, user_id)
        if not conversation:
            return api_error("Conversation not found", 404)
        
        # Add user message
        user_message = LegalAidService.add_message(conversation_id, user_id, content, "user")
        
        # Generate AI response
        import asyncio
        try:
            ai_message = asyncio.run(LegalAidService.generate_ai_response(conversation_id, user_id, content))
        except Exception as e:
            # Fallback to simple response if Claude fails
            ai_message = LegalAidService.add_message(conversation_id, user_id, "I'm sorry, I'm having trouble connecting to my AI services right now. Please try again later.", "ai")
        
        return jsonify({
            "user_message": user_message.to_dict(),
            "ai_message": ai_message.to_dict() if ai_message else None
        })
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Conversation Messages
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations/<conversation_id>/messages", methods=["GET"])
@jwt_required()
def get_conversation_messages(conversation_id):
    user_id = get_jwt_identity()
    
    try:
        messages = LegalAidService.get_conversation_messages(conversation_id, user_id)
        return jsonify([msg.to_dict() for msg in messages])
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Upload Document
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations/<conversation_id>/documents", methods=["POST"])
@jwt_required()
def upload_document(conversation_id):
    user_id = get_jwt_identity()
    
    # Verify user has access to conversation
    conversation = LegalAidService.get_conversation(conversation_id, user_id)
    if not conversation:
        return api_error("Conversation not found", 404)
    
    if 'file' not in request.files:
        return api_error("No file provided", 400, code="VALIDATION_ERROR")
    
    file = request.files['file']
    
    try:
        document = LegalAidService.upload_document(conversation_id, user_id, file)
        return jsonify(document.to_dict()), 201
    except ValueError as e:
        return api_error(str(e), 400, code="VALIDATION_ERROR")
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Share Conversation
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/conversations/<conversation_id>/share", methods=["POST"])
@jwt_required()
def share_conversation(conversation_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    allow_public = data.get("allow_public", False)
    
    try:
        conversation = LegalAidService.share_conversation(
            conversation_id, user_id, allow_public
        )
        if not conversation:
            return api_error("Conversation not found", 404)
        return jsonify(conversation.to_dict())
    except Exception as e:
        return api_error(str(e), 400)


# ---------------------------------------
# Get Categories
# ---------------------------------------
@legal_aid_bp.route("/legal-aid/categories", methods=["GET"])
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
