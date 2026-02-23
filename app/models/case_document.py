from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class CaseDocument(BaseModel):
    __tablename__ = "case_documents"

    # -------------------------
    # Foreign Keys
    # -------------------------
    case_id = db.Column(
        db.String(36),
        db.ForeignKey("cases.id"),
        nullable=False,
        index=True
    )
    uploaded_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # -------------------------
    # File Details
    # -------------------------
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)  # S3 key or local file path
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )  # Soft delete

    # -------------------------
    # Relationships
    # -------------------------
    case = db.relationship(
        "Case",
        back_populates="documents",
        foreign_keys="[CaseDocument.case_id]",
    )
    uploader = db.relationship(
        "User",
        foreign_keys="[CaseDocument.uploaded_by]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "uploaded_by": self.uploaded_by,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "storage_path": self.storage_path,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
