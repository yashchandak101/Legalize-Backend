import time
import logging
from typing import List, Optional, Dict, Any
from ..models.case_ai_suggestion import CaseAISuggestion
from ..repositories.case_ai_suggestion_repository import CaseAISuggestionRepository
from ..services.ai_service import AIService
from ..services.case_assignment_service import CaseAssignmentService
from ..domain.enums import RoleEnum

logger = logging.getLogger(__name__)


class CaseAISuggestionService:

    @staticmethod
    def create_case_suggestion(case_id: str, user_id: str, actor_role: str = None, 
                               async_processing: bool = False) -> CaseAISuggestion:
        """
        Create a case AI suggestion request.
        
        Args:
            case_id: The case ID to generate suggestions for
            user_id: The user ID requesting suggestions
            actor_role: The role of the user
            async_processing: Whether to process asynchronously
            
        Returns:
            CaseAISuggestion: The created suggestion request
            
        Raises:
            ValueError: If unauthorized or invalid
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, actor_role):
            raise ValueError("Unauthorized to access this case")
        
        # Check rate limiting (max 5 suggestions per case per day)
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time(), timezone.utc)
        
        existing_count = CaseAISuggestionRepository.query.filter(
            CaseAISuggestion.case_id == case_id,
            CaseAISuggestion.user_id == user_id,
            CaseAISuggestion.suggestion_type == "case_suggestions",
            CaseAISuggestion.created_at >= start_of_day
        ).count()
        
        if existing_count >= 5:
            raise ValueError("Daily limit of 5 AI suggestions per case reached")
        
        # Get case details
        from ..models.case import Case
        case = Case.query.get(case_id)
        if not case:
            raise ValueError("Case not found")
        
        # Create suggestion request
        suggestion = CaseAISuggestion(
            case_id=case_id,
            user_id=user_id,
            suggestion_type="case_suggestions",
            status="pending",
            request_data={
                "case_title": case.title,
                "case_description": case.description,
                "async_processing": async_processing
            }
        )
        
        suggestion = CaseAISuggestionRepository.create(suggestion)
        
        if not async_processing:
            # Process synchronously
            CaseAISuggestionService._process_case_suggestion(suggestion.id)
        else:
            # Process asynchronously with Celery
            try:
                from ..tasks.celery_tasks import process_ai_suggestion
                process_ai_suggestion.delay(suggestion.id)
            except Exception as e:
                # Fallback to synchronous processing if Celery is not available
                logger.warning(f"Celery not available, processing synchronously: {str(e)}")
                CaseAISuggestionService._process_case_suggestion(suggestion.id)
        
        return suggestion

    @staticmethod
    def get_case_suggestions(case_id: str, user_id: str, user_role: str) -> List[CaseAISuggestion]:
        """
        Get AI suggestions for a case (requires authorization).
        
        Args:
            case_id: The case ID
            user_id: The user ID requesting suggestions
            user_role: The role of the user
            
        Returns:
            List[CaseAISuggestion]: List of suggestions
            
        Raises:
            ValueError: If unauthorized
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, user_role):
            raise ValueError("Unauthorized to access this case")
        
        return CaseAISuggestionRepository.get_suggestions_for_case(
            case_id=case_id,
            suggestion_type="case_suggestions"
        )

    @staticmethod
    def get_user_suggestions(user_id: str) -> List[CaseAISuggestion]:
        """Get all AI suggestions for a user."""
        return CaseAISuggestionRepository.get_suggestions_for_user(user_id)

    @staticmethod
    def get_suggestion_by_id(suggestion_id: str, user_id: str, user_role: str) -> Optional[CaseAISuggestion]:
        """
        Get a specific suggestion by ID (requires authorization).
        
        Args:
            suggestion_id: The suggestion ID
            user_id: The user ID requesting the suggestion
            user_role: The role of the user
            
        Returns:
            CaseAISuggestion: The suggestion or None if not found
            
        Raises:
            ValueError: If unauthorized
        """
        suggestion = CaseAISuggestionRepository.get_by_id(suggestion_id)
        if not suggestion:
            return None
        
        # Check if user can access the case
        from ..services.case_assignment_service import CaseAssignmentService
        if not CaseAssignmentService.can_user_access_case(user_id, suggestion.case_id, user_role):
            raise ValueError("Unauthorized to access this suggestion")
        
        # Users can only see their own suggestions (except admins)
        if suggestion.user_id != user_id and user_role != "admin":
            raise ValueError("Unauthorized to access this suggestion")
        
        return suggestion

    @staticmethod
    def _process_case_suggestion(suggestion_id: str) -> bool:
        """
        Process a case suggestion request (internal method).
        
        Args:
            suggestion_id: The suggestion ID to process
            
        Returns:
            bool: True if successful, False if failed
        """
        suggestion = CaseAISuggestionRepository.get_by_id(suggestion_id)
        if not suggestion:
            return False
        
        start_time = time.time()
        
        try:
            # Get case details
            from ..models.case import Case
            case = Case.query.get(suggestion.case_id)
            if not case:
                raise ValueError("Case not found")
            
            # Get case documents for context
            from ..models.case_document import CaseDocument
            documents = CaseDocument.query.filter_by(
                case_id=suggestion.case_id,
                is_deleted=False
            ).all()
            
            document_data = []
            for doc in documents:
                document_data.append({
                    "id": doc.id,
                    "original_filename": doc.original_filename,
                    "mime_type": doc.mime_type,
                    "size_bytes": doc.size_bytes
                })
            
            # Generate AI suggestions
            ai_service = AIService()
            result = ai_service.generate_case_suggestions(
                case_id=suggestion.case_id,
                case_title=case.title,
                case_description=case.description,
                case_documents=document_data
            )
            
            # Update suggestion with results
            processing_time = int((time.time() - start_time) * 1000)
            
            CaseAISuggestionRepository.update_status(
                suggestion_id=suggestion_id,
                status=result.get("status", "error"),
                suggestions=result.get("suggestions"),
                error_message=result.get("error"),
                provider=result.get("provider"),
                model=result.get("model"),
                processing_time_ms=processing_time
            )
            
            return True
            
        except Exception as e:
            # Update suggestion with error
            processing_time = int((time.time() - start_time) * 1000)
            
            CaseAISuggestionRepository.update_status(
                suggestion_id=suggestion_id,
                status="error",
                error_message=str(e),
                processing_time_ms=processing_time
            )
            
            return False

    @staticmethod
    def create_document_suggestion(document_id: str, user_id: str, actor_role: str = None,
                                   async_processing: bool = False) -> CaseAISuggestion:
        """
        Create a document AI analysis request.
        
        Args:
            document_id: The document ID to analyze
            user_id: The user ID requesting analysis
            actor_role: The role of the user
            async_processing: Whether to process asynchronously
            
        Returns:
            CaseAISuggestion: The created suggestion request
            
        Raises:
            ValueError: If unauthorized or invalid
        """
        # Get document details
        from ..models.case_document import CaseDocument
        document = CaseDocument.query.get(document_id)
        if not document:
            raise ValueError("Document not found")
        
        # Check if user can access the case
        from ..services.case_assignment_service import CaseAssignmentService
        if not CaseAssignmentService.can_user_access_case(user_id, document.case_id, actor_role):
            raise ValueError("Unauthorized to access this document")
        
        # Check rate limiting (max 3 analyses per document per day)
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time(), timezone.utc)
        
        existing_count = CaseAISuggestionRepository.query.filter(
            CaseAISuggestion.case_id == document.case_id,
            CaseAISuggestion.user_id == user_id,
            CaseAISuggestion.suggestion_type == "document_analysis",
            CaseAISuggestion.created_at >= start_of_day
        ).count()
        
        if existing_count >= 3:
            raise ValueError("Daily limit of 3 AI document analyses per case reached")
        
        # Create suggestion request
        suggestion = CaseAISuggestion(
            case_id=document.case_id,
            user_id=user_id,
            suggestion_type="document_analysis",
            status="pending",
            request_data={
                "document_id": document_id,
                "document_filename": document.original_filename,
                "document_type": document.mime_type,
                "async_processing": async_processing
            }
        )
        
        suggestion = CaseAISuggestionRepository.create(suggestion)
        
        if not async_processing:
            # Process synchronously
            CaseAISuggestionService._process_document_suggestion(suggestion.id)
        else:
            # Process asynchronously with Celery
            try:
                from ..tasks.celery_tasks import process_document_analysis
                process_document_analysis.delay(suggestion.id)
            except Exception as e:
                # Fallback to synchronous processing if Celery is not available
                logger.warning(f"Celery not available, processing synchronously: {str(e)}")
                CaseAISuggestionService._process_document_suggestion(suggestion.id)
        
        return suggestion

    @staticmethod
    def _process_document_suggestion(suggestion_id: str) -> bool:
        """
        Process a document suggestion request (internal method).
        
        Args:
            suggestion_id: The suggestion ID to process
            
        Returns:
            bool: True if successful, False if failed
        """
        suggestion = CaseAISuggestionRepository.get_by_id(suggestion_id)
        if not suggestion:
            return False
        
        start_time = time.time()
        
        try:
            # Get document details
            request_data = suggestion.request_data or {}
            document_id = request_data.get("document_id")
            
            if not document_id:
                raise ValueError("Document ID not found in request data")
            
            from ..models.case_document import CaseDocument
            document = CaseDocument.query.get(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Read document content (this is a simplified version)
            # In production, you'd want to extract text from various file types
            document_content = CaseAISuggestionService._extract_document_text(document)
            
            # Determine document type from filename
            document_type = CaseAISuggestionService._classify_document_type(
                document.original_filename,
                document.mime_type
            )
            
            # Generate AI analysis
            ai_service = AIService()
            result = ai_service.analyze_document(
                document_id=document_id,
                document_content=document_content,
                document_type=document_type
            )
            
            # Update suggestion with results
            processing_time = int((time.time() - start_time) * 1000)
            
            CaseAISuggestionRepository.update_status(
                suggestion_id=suggestion_id,
                status=result.get("status", "error"),
                suggestions=result.get("suggestions"),
                error_message=result.get("error"),
                provider=result.get("provider"),
                model=result.get("model"),
                processing_time_ms=processing_time
            )
            
            return True
            
        except Exception as e:
            # Update suggestion with error
            processing_time = int((time.time() - start_time) * 1000)
            
            CaseAISuggestionRepository.update_status(
                suggestion_id=suggestion_id,
                status="error",
                error_message=str(e),
                processing_time_ms=processing_time
            )
            
            return False

    @staticmethod
    def _extract_document_text(document) -> str:
        """Extract text from a document (simplified implementation)."""
        # This is a simplified version - in production you'd use libraries like:
        # - PyPDF2 for PDFs
        # - python-docx for Word documents
        # - textract for various formats
        
        try:
            # Try to read the file as text
            import os
            if os.path.exists(document.storage_path):
                with open(document.storage_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Limit content length for API
                    return content[:10000] if len(content) > 10000 else content
        except Exception:
            pass
        
        # Fallback placeholder text
        return f"Document: {document.original_filename}\nType: {document.mime_type}\nSize: {document.size_bytes} bytes"

    @staticmethod
    def _classify_document_type(filename: str, mime_type: str) -> str:
        """Classify document type based on filename and MIME type."""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return 'pdf'
        elif filename_lower.endswith(('.doc', '.docx')):
            return 'contract'
        elif filename_lower.endswith(('.txt', '.rtf')):
            return 'text_document'
        elif filename_lower.endswith(('.xls', '.xlsx', '.csv')):
            return 'spreadsheet'
        elif filename_lower.endswith(('.ppt', '.pptx')):
            return 'presentation'
        elif 'contract' in filename_lower or 'agreement' in filename_lower:
            return 'contract'
        elif 'brief' in filename_lower:
            return 'legal_brief'
        elif 'motion' in filename_lower:
            return 'legal_motion'
        else:
            return 'unknown'
