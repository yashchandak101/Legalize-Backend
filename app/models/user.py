import uuid
from ..core.extensions import db
from .base import BaseModel
from app.domain.enums import RoleEnum
from passlib.hash import bcrypt


class User(BaseModel):
    __tablename__ = "users"

    # --- Primary Key (UUID) ---
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # --- Core Fields ---
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=RoleEnum.USER.value)
    name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # --- Relationships ---
    lawyer_profile = db.relationship(
        "LawyerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    cases = db.relationship(
        "Case",
        back_populates="client",
        foreign_keys="[Case.user_id]",
        lazy=True,
    )
    appointments_as_client = db.relationship(
        "Appointment",
        foreign_keys="[Appointment.client_id]",
        back_populates="client",
        lazy=True,
    )
    appointments_as_lawyer = db.relationship(
        "Appointment",
        foreign_keys="[Appointment.lawyer_id]",
        back_populates="lawyer",
        lazy=True,
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        foreign_keys="[Notification.user_id]",
        cascade="all, delete-orphan"
    )

    # --- Password Handling ---
    def set_password(self, raw_password: str):
        """Hashes and sets the user's password."""
        self.password = bcrypt.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifies a raw password against the stored hash."""
        return bcrypt.verify(raw_password, self.password)