from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalAidMessage(BaseModel):
    __tablename__ = "legal_aid_messages"

    # -------------------------
    # Message Details
    # -------------------------
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default="user")  # user, ai, system

    # -------------------------
    # AI Analysis
    # -------------------------
    ai_confidence = db.Column(db.Float)
    ai_sources = db.Column(db.Text)

    # -------------------------
    # Foreign Keys
    # -------------------------
    conversation_id = db.Column(
        db.String(36),
        db.ForeignKey("legal_aid_conversations.id"),
        nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    conversation = db.relationship(
        "LegalAidConversation",
        back_populates="messages"
    )
    user = db.relationship(
        "User",
        backref="legal_aid_messages"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "message_type": self.message_type,
            "ai_confidence": self.ai_confidence,
            "ai_sources": self.ai_sources,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
        }
