import os
import uuid
from typing import Optional, List
from werkzeug.utils import secure_filename
from ..models.case_document import CaseDocument
from ..repositories.case_document_repository import CaseDocumentRepository
from ..domain.enums import RoleEnum


class CaseDocumentService:

    # Allowed file types and max size (in bytes)
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'txt', 'rtf',
        'jpg', 'jpeg', 'png', 'gif', 'bmp',
        'xls', 'xlsx', 'csv', 'ppt', 'pptx'
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in CaseDocumentService.ALLOWED_EXTENSIONS)

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename for storage."""
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())
        return f"{unique_id}.{file_ext}" if file_ext else unique_id

    @staticmethod
    def save_uploaded_file(file, case_id: str, user_id: str, actor_role: str = None) -> CaseDocument:
        """
        Save an uploaded file to storage and create database record.
        
        Args:
            file: The uploaded file object
            case_id: The case ID
            user_id: The user ID uploading the file
            actor_role: The role of the user
            
        Returns:
            CaseDocument: The created document record
            
        Raises:
            ValueError: If unauthorized or invalid file
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, actor_role):
            raise ValueError("Unauthorized to access this case")
        
        # Validate file
        if not file or not file.filename:
            raise ValueError("No file provided")
        
        if not CaseDocumentService.is_allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > CaseDocumentService.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        # Generate unique filename and save file
        original_filename = secure_filename(file.filename)
        unique_filename = CaseDocumentService.generate_unique_filename(original_filename)
        
        # For now, save to local storage (can be extended to S3)
        upload_dir = os.path.join('uploads', 'case_documents', case_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        storage_path = os.path.join(upload_dir, unique_filename)
        file.save(storage_path)
        
        # Create database record
        document = CaseDocument(
            case_id=case_id,
            uploaded_by=user_id,
            filename=unique_filename,
            original_filename=original_filename,
            mime_type=file.content_type or 'application/octet-stream',
            size_bytes=file_size,
            storage_path=storage_path
        )
        
        return CaseDocumentRepository.create(document)
        
        # Create notification for case owner and assigned lawyer
        from ..services.notification_service import NotificationService
        from ..models.case import Case
        
        # Get case details
        document_with_case = db.session.query(Case).filter_by(id=document.case_id).first()
        if document_with_case:
            # Notify case owner
            NotificationService.create_document_notification(
                user_id=document_with_case.user_id,
                case_id=document.case_id,
                document_id=document.id,
                filename=document.original_filename
            )
            
            # Notify assigned lawyer if exists
            if document_with_case.assigned_lawyer_id:
                NotificationService.create_document_notification(
                    user_id=document_with_case.assigned_lawyer_id,
                    case_id=document.case_id,
                    document_id=document.id,
                    filename=document.original_filename
                )
        
        return document

    @staticmethod
    def get_case_documents(case_id: str, user_id: str, user_role: str) -> List[CaseDocument]:
        """
        Get documents for a case.
        
        Args:
            case_id: The case ID
            user_id: The user ID requesting documents
            user_role: The role of the user
            
        Returns:
            List[CaseDocument]: List of documents
            
        Raises:
            ValueError: If unauthorized
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, user_role):
            raise ValueError("Unauthorized to access this case")
        
        return CaseDocumentRepository.get_documents_for_case(case_id, include_deleted=False)

    @staticmethod
    def get_document_by_id(document_id: str, user_id: str, user_role: str) -> Optional[CaseDocument]:
        """
        Get a specific document by ID.
        
        Args:
            document_id: The document ID
            user_id: The user ID requesting the document
            user_role: The role of the user
            
        Returns:
            CaseDocument: The document or None if not found
            
        Raises:
            ValueError: If unauthorized
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        document = CaseDocumentRepository.get_by_id(document_id)
        if not document:
            return None
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, document.case_id, user_role):
            raise ValueError("Unauthorized to access this document")
        
        # Don't return deleted documents
        if document.is_deleted:
            return None
        
        return document

    @staticmethod
    def delete_document(document_id: str, user_id: str, actor_role: str = None) -> bool:
        """
        Soft delete a document.
        
        Args:
            document_id: The document ID to delete
            user_id: The user ID deleting the document
            actor_role: The role of the user
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            ValueError: If unauthorized
        """
        document = CaseDocumentRepository.get_user_document(document_id, user_id)
        if not document:
            return False
        
        # Users can only delete their own documents
        CaseDocumentRepository.soft_delete(document)
        return True

    @staticmethod
    def get_file_path(document: CaseDocument) -> str:
        """Get the file path for a document."""
        return document.storage_path

    @staticmethod
    def can_user_access_document(document_id: str, user_id: str, user_role: str) -> bool:
        """
        Check if a user can access a specific document.
        
        Args:
            document_id: The document ID
            user_id: The user ID
            user_role: The role of the user
            
        Returns:
            bool: True if user can access the document
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        document = CaseDocumentRepository.get_by_id(document_id)
        if not document or document.is_deleted:
            return False
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, document.case_id, user_role):
            return False
        
        return True
