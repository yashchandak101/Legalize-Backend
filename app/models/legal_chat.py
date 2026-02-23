from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalChat(BaseModel):
    __tablename__ = "legal_chats"

    # -------------------------
    # Chat Details
    # -------------------------
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # family, criminal, civil, corporate, etc.
    status = db.Column(db.String(50), default="active")  # active, lawyer_requested, closed

    # -------------------------
    # AI Context
    # -------------------------
    ai_context = db.Column(db.Text)  # AI context for the conversation
    summary = db.Column(db.Text)  # AI-generated summary of the conversation

    # -------------------------
    # Lawyer Request
    # -------------------------
    lawyer_requested = db.Column(db.Boolean, default=False)
    lawyer_request_reason = db.Column(db.Text)
    lawyer_assigned_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

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
        "LegalChatMessage",
        back_populates="chat",
        foreign_keys="[LegalChatMessage.chat_id]",
        cascade="all, delete-orphan",
        order_by="LegalChatMessage.created_at"
    )
    documents = db.relationship(
        "LegalChatDocument",
        back_populates="chat",
        foreign_keys="[LegalChatDocument.chat_id]",
        cascade="all, delete-orphan"
    )
    user = db.relationship(
        "User",
        backref="legal_chats"
    )
    assigned_lawyer = db.relationship(
        "User",
        foreign_keys=[lawyer_assigned_id],
        backref="assigned_chats"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "ai_context": self.ai_context,
            "summary": self.summary,
            "lawyer_requested": self.lawyer_requested,
            "lawyer_request_reason": self.lawyer_request_reason,
            "lawyer_assigned_id": self.lawyer_assigned_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "message_count": len(self.messages) if self.messages else 0,
            "last_message": self.messages[-1].to_dict() if self.messages and len(self.messages) > 0 else None,
        }
