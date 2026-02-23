from ..models.lawyer_profile import LawyerProfile
from ..core.extensions import db


class LawyerProfileRepository:

    @staticmethod
    def create(profile: LawyerProfile):
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def get_by_id(profile_id: str):
        return LawyerProfile.query.get(profile_id)

    @staticmethod
    def get_by_user_id(user_id: str):
        return LawyerProfile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def update(profile: LawyerProfile):
        db.session.commit()
        return profile

    @staticmethod
    def delete(profile: LawyerProfile):
        db.session.delete(profile)
        db.session.commit()

    @staticmethod
    def get_all():
        return LawyerProfile.query.all()

    @staticmethod
    def get_by_bar_number(bar_number: str):
        return LawyerProfile.query.filter_by(bar_number=bar_number).first()
