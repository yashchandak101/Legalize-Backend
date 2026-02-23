from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class CaseAssignment(BaseModel):
    __tablename__ = "case_assignments"

    # -------------------------
    # Foreign Keys
    # -------------------------
    case_id = db.Column(
        db.String(36),
        db.ForeignKey("cases.id"),
        nullable=False,
        index=True
    )
    lawyer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    assigned_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # -------------------------
    # Assignment Details
    # -------------------------
    assigned_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    status = db.Column(
        db.String(20),
        default="active",
        nullable=False
    )  # active | superseded

    # -------------------------
    # Relationships
    # -------------------------
    case = db.relationship(
        "Case",
        back_populates="assignments",
        foreign_keys="[CaseAssignment.case_id]",
    )
    lawyer = db.relationship(
        "User",
        foreign_keys="[CaseAssignment.lawyer_id]",
    )
    assigned_by_user = db.relationship(
        "User",
        foreign_keys="[CaseAssignment.assigned_by]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "lawyer_id": self.lawyer_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }