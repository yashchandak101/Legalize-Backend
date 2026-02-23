from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class CaseComment(BaseModel):
    __tablename__ = "case_comments"

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
    # Comment Details
    # -------------------------
    body = db.Column(db.Text, nullable=False)
    is_internal = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )  # Only visible to lawyers/admins if true

    # -------------------------
    # Relationships
    # -------------------------
    case = db.relationship(
        "Case",
        back_populates="comments",
        foreign_keys="[CaseComment.case_id]",
    )
    author = db.relationship(
        "User",
        foreign_keys="[CaseComment.user_id]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "body": self.body,
            "is_internal": self.is_internal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
