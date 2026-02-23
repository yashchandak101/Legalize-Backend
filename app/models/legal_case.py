from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalCase(BaseModel):
    __tablename__ = "legal_cases"

    # -------------------------
    # Case Details
    # -------------------------
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # family, criminal, civil, corporate, etc.
    urgency = db.Column(db.String(20), default="medium")  # low, medium, high, urgent
    status = db.Column(db.String(50), default="active")  # active, lawyer_assigned, closed

    # -------------------------
    # AI Analysis
    # -------------------------
    ai_context = db.Column(db.Text)  # AI context for the conversation
    ai_summary = db.Column(db.Text)  # AI-generated summary of the case
    ai_recommendations = db.Column(db.Text)  # AI recommendations
    ai_confidence_score = db.Column(db.Float)  # AI confidence in analysis

    # -------------------------
    # Sharing & Collaboration
    # -------------------------
    is_shared = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(255), unique=True, nullable=True)  # Unique token for sharing
    shared_with_users = db.Column(db.Text)  # JSON array of user IDs this case is shared with
    allow_public_view = db.Column(db.Boolean, default=False)  # Allow public view with share link

    # -------------------------
    # Lawyer Assignment
    # -------------------------
    lawyer_requested = db.Column(db.Boolean, default=False)
    lawyer_request_reason = db.Column(db.Text)
    assigned_lawyer_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    lawyer_assigned_at = db.Column(db.DateTime(timezone=True))

    # -------------------------
    # User Information
    # -------------------------
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    messages = db.relationship(
        "LegalCaseMessage",
        back_populates="case",
        foreign_keys="[LegalCaseMessage.case_id]",
        cascade="all, delete-orphan",
        order_by="LegalCaseMessage.created_at"
    )
    documents = db.relationship(
        "LegalCaseDocument",
        back_populates="case",
        foreign_keys="[LegalCaseDocument.case_id]",
        cascade="all, delete-orphan"
    )
    shared_access = db.relationship(
        "LegalCaseShare",
        back_populates="case",
        foreign_keys="[LegalCaseShare.case_id]",
        cascade="all, delete-orphan"
    )
    user = db.relationship(
        "User",
        backref="legal_cases"
    )
    assigned_lawyer = db.relationship(
        "User",
        foreign_keys=[assigned_lawyer_id],
        backref="assigned_legal_cases"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self, include_shared=False):
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "urgency": self.urgency,
            "status": self.status,
            "ai_context": self.ai_context,
            "ai_summary": self.ai_summary,
            "ai_recommendations": self.ai_recommendations,
            "ai_confidence_score": self.ai_confidence_score,
            "is_shared": self.is_shared,
            "share_token": self.share_token,
            "allow_public_view": self.allow_public_view,
            "lawyer_requested": self.lawyer_requested,
            "lawyer_request_reason": self.lawyer_request_reason,
            "assigned_lawyer_id": self.assigned_lawyer_id,
            "lawyer_assigned_at": self.lawyer_assigned_at.isoformat() if self.lawyer_assigned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "message_count": len(self.messages) if self.messages else 0,
            "document_count": len(self.documents) if self.documents else 0,
            "last_message": self.messages[-1].to_dict() if self.messages and len(self.messages) > 0 else None,
        }
        
        if include_shared:
            result["shared_with"] = [share.to_dict() for share in self.shared_access]
            
        return result
