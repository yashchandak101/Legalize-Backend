from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalAidConversation(BaseModel):
    __tablename__ = "legal_aid_conversations"

    # -------------------------
    # Conversation Details
    # -------------------------
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)
    
    # -------------------------
    # Sharing
    # -------------------------
    is_shared = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(255), unique=True, nullable=True)
    allow_public_view = db.Column(db.Boolean, default=False)

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
        "LegalAidMessage",
        back_populates="conversation",
        foreign_keys="[LegalAidMessage.conversation_id]",
        cascade="all, delete-orphan",
        order_by="LegalAidMessage.created_at"
    )
    documents = db.relationship(
        "LegalAidDocument",
        back_populates="conversation",
        foreign_keys="[LegalAidDocument.conversation_id]",
        cascade="all, delete-orphan"
    )
    user = db.relationship(
        "User",
        backref="legal_aid_conversations"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "is_shared": self.is_shared,
            "share_token": self.share_token,
            "allow_public_view": self.allow_public_view,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "message_count": len(self.messages) if self.messages else 0,
            "document_count": len(self.documents) if self.documents else 0,
            "last_message": self.messages[-1].to_dict() if self.messages and len(self.messages) > 0 else None,
        }
