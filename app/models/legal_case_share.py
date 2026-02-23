from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalCaseShare(BaseModel):
    __tablename__ = "legal_case_shares"

    # -------------------------
    # Share Details
    # -------------------------
    permission_level = db.Column(db.String(20), default="view")  # view, comment, edit
    message = db.Column(db.Text)  # Optional message when sharing

    # -------------------------
    # Foreign Keys
    # -------------------------
    case_id = db.Column(
        db.String(36),
        db.ForeignKey("legal_cases.id"),
        nullable=False
    )
    shared_by_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )
    shared_with_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True  # Can be null for public shares
    )

    # Relationships
    case = db.relationship(
        "LegalCase",
        back_populates="shared_access"
    )
    shared_by_user = db.relationship(
        "User",
        foreign_keys=[shared_by_user_id],
        backref="shared_cases"
    )
    shared_with_user = db.relationship(
        "User",
        foreign_keys=[shared_with_user_id],
        backref="shared_with_me"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "permission_level": self.permission_level,
            "message": self.message,
            "case_id": self.case_id,
            "shared_by_user_id": self.shared_by_user_id,
            "shared_with_user_id": self.shared_with_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
