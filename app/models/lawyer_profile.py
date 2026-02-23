from .base import BaseModel
from ..core.extensions import db


class LawyerProfile(BaseModel):
    __tablename__ = "lawyer_profiles"

    # -------------------------
    # Foreign Key
    # -------------------------
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # -------------------------
    # Professional Information
    # -------------------------
    bar_number = db.Column(db.String(50), nullable=True)
    bar_state = db.Column(db.String(2), nullable=True)  # US state code
    bio = db.Column(db.Text, nullable=True)
    specializations = db.Column(db.Text, nullable=True)  # JSON string or comma-separated
    hourly_rate_cents = db.Column(db.Integer, nullable=True)

    # -------------------------
    # Relationships
    # -------------------------
    user = db.relationship(
        "User",
        back_populates="lawyer_profile",
        foreign_keys="[LawyerProfile.user_id]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bar_number": self.bar_number,
            "bar_state": self.bar_state,
            "bio": self.bio,
            "specializations": self.specializations,
            "hourly_rate_cents": self.hourly_rate_cents,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }