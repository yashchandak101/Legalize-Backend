from ..models.case_ai_suggestion import CaseAISuggestion
from ..core.extensions import db


class CaseAISuggestionRepository:

    @staticmethod
    def create(suggestion: CaseAISuggestion):
        db.session.add(suggestion)
        db.session.commit()
        return suggestion

    @staticmethod
    def get_by_id(suggestion_id: str):
        return CaseAISuggestion.query.get(suggestion_id)

    @staticmethod
    def get_suggestions_for_case(case_id: str, suggestion_type: str = None):
        """Get AI suggestions for a case, optionally filtered by type."""
        query = CaseAISuggestion.query.filter_by(case_id=case_id)
        
        if suggestion_type:
            query = query.filter_by(suggestion_type=suggestion_type)
        
        return query.order_by(CaseAISuggestion.created_at.desc()).all()

    @staticmethod
    def get_suggestions_for_user(user_id: str, suggestion_type: str = None):
        """Get AI suggestions for a user, optionally filtered by type."""
        query = CaseAISuggestion.query.filter_by(user_id=user_id)
        
        if suggestion_type:
            query = query.filter_by(suggestion_type=suggestion_type)
        
        return query.order_by(CaseAISuggestion.created_at.desc()).all()

    @staticmethod
    def get_latest_suggestion(case_id: str, suggestion_type: str):
        """Get the latest suggestion for a case of a specific type."""
        return CaseAISuggestion.query.filter_by(
            case_id=case_id,
            suggestion_type=suggestion_type
        ).order_by(CaseAISuggestion.created_at.desc()).first()

    @staticmethod
    def update(suggestion: CaseAISuggestion):
        db.session.commit()
        return suggestion

    @staticmethod
    def update_status(suggestion_id: str, status: str, suggestions: dict = None, 
                      error_message: str = None, provider: str = None, model: str = None,
                      processing_time_ms: int = None):
        """Update suggestion status and results."""
        suggestion = CaseAISuggestion.query.get(suggestion_id)
        if suggestion:
            suggestion.status = status
            if suggestions is not None:
                suggestion.suggestions = suggestions
            if error_message is not None:
                suggestion.error_message = error_message
            if provider is not None:
                suggestion.provider = provider
            if model is not None:
                suggestion.model = model
            if processing_time_ms is not None:
                suggestion.processing_time_ms = processing_time_ms
            
            db.session.commit()
        return suggestion

    @staticmethod
    def delete(suggestion: CaseAISuggestion):
        db.session.delete(suggestion)
        db.session.commit()

    @staticmethod
    def get_pending_suggestions():
        """Get all pending suggestions for background processing."""
        return CaseAISuggestion.query.filter_by(status="pending").all()

    @staticmethod
    def count_suggestions_for_case(case_id: str, suggestion_type: str = None):
        """Count suggestions for a case, optionally filtered by type."""
        query = CaseAISuggestion.query.filter_by(case_id=case_id)
        
        if suggestion_type:
            query = query.filter_by(suggestion_type=suggestion_type)
        
        return query.count()
