from ..models.payment import Payment
from ..core.extensions import db


class PaymentRepository:

    @staticmethod
    def create(payment: Payment):
        db.session.add(payment)
        db.session.commit()
        return payment

    @staticmethod
    def get_by_id(payment_id: str):
        return Payment.query.get(payment_id)

    @staticmethod
    def get_by_stripe_payment_intent_id(stripe_payment_intent_id: str):
        return Payment.query.filter_by(stripe_payment_intent_id=stripe_payment_intent_id).first()

    @staticmethod
    def get_payments_for_user(user_id: str):
        return Payment.query.filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()

    @staticmethod
    def get_payments_for_case(case_id: str):
        return Payment.query.filter_by(case_id=case_id).order_by(Payment.created_at.desc()).all()

    @staticmethod
    def update(payment: Payment):
        db.session.commit()
        return payment

    @staticmethod
    def update_status(payment_id: str, status: str, stripe_charge_id: str = None):
        payment = Payment.query.get(payment_id)
        if payment:
            payment.status = status
            if stripe_charge_id:
                payment.stripe_charge_id = stripe_charge_id
            if status == "completed":
                from datetime import datetime, timezone
                payment.completed_at = datetime.now(timezone.utc)
            elif status == "refunded":
                from datetime import datetime, timezone
                payment.refunded_at = datetime.now(timezone.utc)
            db.session.commit()
        return payment

    @staticmethod
    def delete(payment: Payment):
        db.session.delete(payment)
        db.session.commit()
