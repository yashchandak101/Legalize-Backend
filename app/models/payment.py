from datetime import datetime, timezone
from .base import BaseModel
from ..core.extensions import db


class Payment(BaseModel):
    __tablename__ = "payments"

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
    # Payment Details
    # -------------------------
    amount_cents = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), nullable=False, default="usd")
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )  # pending | completed | failed | refunded
    
    # Stripe integration fields
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True, unique=True)
    stripe_client_secret = db.Column(db.String(255), nullable=True)
    stripe_charge_id = db.Column(db.String(255), nullable=True)
    
    # Payment metadata
    description = db.Column(db.Text, nullable=True)
    payment_metadata = db.Column(db.JSON, nullable=True)  # Additional payment data
    
    # Timestamps
    completed_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)

    # -------------------------
    # Relationships
    # -------------------------
    case = db.relationship(
        "Case",
        back_populates="payments",
        foreign_keys="[Payment.case_id]",
    )
    user = db.relationship(
        "User",
        foreign_keys="[Payment.user_id]",
    )

    # -------------------------
    # Serializer
    # -------------------------
    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "description": self.description,
            "metadata": self.payment_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
        }
