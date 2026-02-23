from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class CaseAISuggestion(BaseModel):
    __tablename__ = "case_ai_suggestions"

    # -------------------------
    # Foreign Keys
    # -------------------------
    case_id = db.Column(
        db.String(36),
        db.ForeignKey("cases.id"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # -------------------------
    # Suggestion Details
    # -------------------------
    suggestion_type = db.Column(db.String(50), nullable=False)  # case_suggestions, document_analysis
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, completed, error
    
    # AI Provider and Model Info
    provider = db.Column(db.String(50), nullable=True)  # openai, anthropic, mock
    model = db.Column(db.String(100), nullable=True)
    
    # AI Response Data
    suggestions = db.Column(db.JSON, nullable=True)  # The actual AI suggestions
    error_message = db.Column(db.Text, nullable=True)  # Error if failed
    
    # Request metadata
    request_data = db.Column(db.JSON, nullable=True)  # Original request data
    processing_time_ms = db.Column(db.Integer, nullable=True)  # Processing time in milliseconds

    # -------------------------
    # Relationships
    # -------------------------
    case = db.relationship(
        "Case",
        foreign_keys="[CaseAISuggestion.case_id]",
    )
    user = db.relationship(
        "User",
        foreign_keys="[CaseAISuggestion.user_id]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "suggestion_type": self.suggestion_type,
            "status": self.status,
            "provider": self.provider,
            "model": self.model,
            "suggestions": self.suggestions,
            "error_message": self.error_message,
            "request_data": self.request_data,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # -------------------------
    # Helper methods
    # -------------------------
    def is_completed(self) -> bool:
        """Check if suggestion processing is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if suggestion processing failed."""
        return self.status == "error"

    def is_pending(self) -> bool:
        """Check if suggestion is still pending."""
        return self.status == "pending"
