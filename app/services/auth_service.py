from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from app.domain.enums import RoleEnum
from ..models.user import User
from ..repositories.user_repository import UserRepository


class AuthService:

    @staticmethod
    def register(email: str, password: str, role: str):

        # ✅ Validate role
        if role not in [r.value for r in RoleEnum]:
            raise ValueError("Invalid role")

        # ✅ Check existing user
        existing = UserRepository.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        hashed_password = generate_password_hash(password)

        user = User(
            email=email,
            password=hashed_password,
            role=role,
        )

        return UserRepository.create(user)

    @staticmethod
    def login(email: str, password: str):

        user = UserRepository.get_by_email(email)

        if not user or not check_password_hash(user.password, password):
            raise ValueError("Invalid credentials")

        # ✅ Embed role inside JWT
        additional_claims = {
            "role": user.role
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        refresh_token = create_refresh_token(
            identity=str(user.id)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            },
        }

    @staticmethod
    def get_user_by_id(user_id: str):
        """Get user by ID."""
        return UserRepository.get_by_id(user_id)