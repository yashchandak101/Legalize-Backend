from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalCaseMessage(BaseModel):
    __tablename__ = "legal_case_messages"

    # -------------------------
    # Message Details
    # -------------------------
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default="user")  # user, ai, system, lawyer

    # -------------------------
    # AI Analysis
    # -------------------------
    ai_confidence = db.Column(db.Float)  # AI confidence in response
    ai_sources = db.Column(db.Text)  # Legal sources/references used by AI

    # -------------------------
    # Foreign Keys
    # -------------------------
    case_id = db.Column(
        db.String(36),
        db.ForeignKey("legal_cases.id"),
        nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    case = db.relationship(
        "LegalCase",
        back_populates="messages"
    )
    user = db.relationship(
        "User",
        backref="legal_case_messages"
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
            "case_id": self.case_id,
            "user_id": self.user_id,
        }
