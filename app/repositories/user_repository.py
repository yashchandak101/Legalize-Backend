from ..models.user import User
from ..core.extensions import db


class UserRepository:

    @staticmethod
    def create(user: User):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_by_email(email: str):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_by_id(user_id: str):
        return User.query.get(user_id)