from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class LegalChatDocument(BaseModel):
    __tablename__ = "legal_chat_documents"

    # -------------------------
    # Document Details
    # -------------------------
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, txt, etc.
    mime_type = db.Column(db.String(100), nullable=False)

    # -------------------------
    # Content Analysis
    # -------------------------
    extracted_text = db.Column(db.Text)  # Extracted text from document
    ai_summary = db.Column(db.Text)  # AI summary of document content

    # -------------------------
    # Foreign Keys
    # -------------------------
    chat_id = db.Column(
        db.String(36),
        db.ForeignKey("legal_chats.id"),
        nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    chat = db.relationship(
        "LegalChat",
        back_populates="documents"
    )
    user = db.relationship(
        "User",
        backref="legal_chat_documents"
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "extracted_text": self.extracted_text,
            "ai_summary": self.ai_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
        }
