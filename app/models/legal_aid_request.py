from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalAidRequest(BaseModel):
    __tablename__ = "legal_aid_requests"

    # -------------------------
    # Request Details
    # -------------------------
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # family, criminal, civil, corporate, etc.
    urgency = db.Column(db.String(20), default="medium")  # low, medium, high, urgent
    status = db.Column(db.String(50), default="open")  # open, processing, completed, closed

    # -------------------------
    # AI Analysis
    # -------------------------
    ai_summary = db.Column(db.Text)  # AI-generated summary
    ai_recommendations = db.Column(db.Text)  # AI recommendations
    ai_legal_references = db.Column(db.Text)  # Legal references suggested by AI
    ai_confidence_score = db.Column(db.Float)  # AI confidence in analysis

    # -------------------------
    # User Information
    # -------------------------
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    documents = db.relationship(
        "LegalAidDocument",
        back_populates="request",
        foreign_keys="[LegalAidDocument.request_id]",
        cascade="all, delete-orphan"
    )
    user = db.relationship(
        "User",
        backref="legal_aid_requests"
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
            "urgency": self.urgency,
            "status": self.status,
            "ai_summary": self.ai_summary,
            "ai_recommendations": self.ai_recommendations,
            "ai_legal_references": self.ai_legal_references,
            "ai_confidence_score": self.ai_confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
        }
