import os
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.datastructures import FileStorage

from app.services.case_document_service import CaseDocumentService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be case_document_bp
case_document_bp = Blueprint("case_document_bp", __name__)


# ---------------------------------------
# Upload Document
# ---------------------------------------
@case_document_bp.route("/cases/<case_id>/documents", methods=["POST"])
@jwt_required()
def upload_document(case_id):
    user_id = get_jwt_identity()
    
    # Check if file is present
    if 'file' not in request.files:
        return api_error("No file provided", 400, code="VALIDATION_ERROR")
    
    file = request.files['file']
    if file.filename == '':
        return api_error("No file selected", 400, code="VALIDATION_ERROR")
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        document = CaseDocumentService.save_uploaded_file(
            file=file,
            case_id=case_id,
            user_id=user_id,
            actor_role=user.role
        )
        return jsonify(document.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Case Documents
# ---------------------------------------
@case_document_bp.route("/cases/<case_id>/documents", methods=["GET"])
@jwt_required()
def get_case_documents(case_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        documents = CaseDocumentService.get_case_documents(
            case_id=case_id,
            user_id=user_id,
            user_role=user.role
        )
        return jsonify([doc.to_dict() for doc in documents]), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Document by ID
# ---------------------------------------
@case_document_bp.route("/documents/<document_id>", methods=["GET"])
@jwt_required()
def get_document(document_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        document = CaseDocumentService.get_document_by_id(
            document_id=document_id,
            user_id=user_id,
            user_role=user.role
        )
        
        if not document:
            return api_error("Document not found", 404, code="NOT_FOUND")
        
        return jsonify(document.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Download Document
# ---------------------------------------
@case_document_bp.route("/documents/<document_id>/download", methods=["GET"])
@jwt_required()
def download_document(document_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        document = CaseDocumentService.get_document_by_id(
            document_id=document_id,
            user_id=user_id,
            user_role=user.role
        )
        
        if not document:
            return api_error("Document not found", 404, code="NOT_FOUND")
        
        file_path = CaseDocumentService.get_file_path(document)
        
        if not os.path.exists(file_path):
            return api_error("File not found on server", 404, code="NOT_FOUND")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type
        )
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Delete Document
# ---------------------------------------
@case_document_bp.route("/documents/<document_id>", methods=["DELETE"])
@jwt_required()
def delete_document(document_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        deleted = CaseDocumentService.delete_document(
            document_id=document_id,
            user_id=user_id,
            actor_role=user.role
        )
        
        if not deleted:
            return api_error("Document not found", 404, code="NOT_FOUND")
        
        return jsonify({"message": "Document deleted successfully"}), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Document Info (metadata only)
# ---------------------------------------
@case_document_bp.route("/documents/<document_id>/info", methods=["GET"])
@jwt_required()
def get_document_info(document_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        if not CaseDocumentService.can_user_access_document(
            document_id=document_id,
            user_id=user_id,
            user_role=user.role
        ):
            return api_error("Unauthorized", 403, code="FORBIDDEN")
        
        document = CaseDocumentService.get_document_by_id(document_id, user_id, user.role)
        if not document:
            return api_error("Document not found", 404, code="NOT_FOUND")
        
        # Return metadata without file path
        metadata = {
            "id": document.id,
            "case_id": document.case_id,
            "uploaded_by": document.uploaded_by,
            "filename": document.original_filename,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
        }
        
        return jsonify(metadata), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)
