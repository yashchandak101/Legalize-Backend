from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class Notification(BaseModel):
    __tablename__ = "notifications"

    # -------------------------
    # Foreign Keys
    # -------------------------
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # -------------------------
    # Notification Details
    # -------------------------
    kind = db.Column(db.String(50), nullable=False)  # e.g. case_assigned, payment_received, etc.
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    # Optional payload for additional data
    payload = db.Column(db.JSON, nullable=True)
    
    # Read status
    read_at = db.Column(db.DateTime, nullable=True)
    
    # -------------------------
    # Relationships
    # -------------------------
    user = db.relationship(
        "User",
        foreign_keys="[Notification.user_id]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "payload": self.payload,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # -------------------------
    # Helper methods
    # -------------------------
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read_at:
            self.read_at = datetime.now(timezone.utc)
            db.session.commit()

    def is_read(self) -> bool:
        """Check if notification is read."""
        return self.read_at is not None