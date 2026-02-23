from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class Case(BaseModel):
    __tablename__ = "cases"

    # -------------------------
    # Case Details
    # -------------------------
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(50),
        default="open",
        nullable=False
    )  # open | in_progress | assigned | closed (see domain/case_rules.py)

    # -------------------------
    # Foreign Keys (UUID String)
    # -------------------------
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )
    assigned_lawyer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # Relationships
    assignments = db.relationship(
        "CaseAssignment",
        back_populates="case",
        foreign_keys="[CaseAssignment.case_id]",
        cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "CaseComment",
        back_populates="case",
        foreign_keys="[CaseComment.case_id]",
        cascade="all, delete-orphan"
    )
    documents = db.relationship(
        "CaseDocument",
        back_populates="case",
        foreign_keys="[CaseDocument.case_id]",
        cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment",
        back_populates="case",
        foreign_keys="[Payment.case_id]",
        cascade="all, delete-orphan"
    )
    client = db.relationship(
        "User",
        back_populates="cases",
        foreign_keys="[Case.user_id]",
    )
    assigned_lawyer = db.relationship(
        "User",
        foreign_keys="[Case.assigned_lawyer_id]",
        backref="assigned_cases"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "assigned_lawyer_id": self.assigned_lawyer_id,
        }