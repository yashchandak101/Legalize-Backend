import os
from typing import Optional
from ..models.payment import Payment
from ..repositories.payment_repository import PaymentRepository
from ..services.case_assignment_service import CaseAssignmentService
from ..domain.enums import RoleEnum
from ..core.extensions import db


class PaymentService:

    @staticmethod
    def create_payment_intent(case_id: str, user_id: str, amount_cents: int, 
                           description: str = None, actor_role: str = None) -> Payment:
        """
        Create a payment intent using Stripe.
        
        Args:
            case_id: The case ID to create payment for
            user_id: The user ID creating the payment
            amount_cents: Amount in cents
            description: Optional description
            actor_role: The role of the user
            
        Returns:
            Payment: The created payment record
            
        Raises:
            ValueError: If unauthorized or invalid
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, actor_role):
            raise ValueError("Unauthorized to access this case")
        
        # Validate amount
        if amount_cents <= 0:
            raise ValueError("Amount must be greater than 0")
        
        # Create payment record
        payment = Payment(
            case_id=case_id,
            user_id=user_id,
            amount_cents=amount_cents,
            description=description,
            status="pending"
        )
        
        payment = PaymentRepository.create(payment)
        
        # Create Stripe Payment Intent
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                description=description,
                payment_metadata={
                    "payment_id": payment.id,
                    "case_id": case_id,
                    "user_id": user_id
                }
            )
            
            # Update payment with Stripe details
            payment.stripe_payment_intent_id = intent.id
            payment.stripe_client_secret = intent.client_secret
            PaymentRepository.update(payment)
            
        except Exception as e:
            # If Stripe fails, delete the payment record
            PaymentRepository.delete(payment)
            raise ValueError(f"Stripe payment creation failed: {str(e)}")
        
        return payment

    @staticmethod
    def get_user_payments(user_id: str):
        """Get all payments for a user."""
        return PaymentRepository.get_payments_for_user(user_id)

    @staticmethod
    def get_payment_by_id(payment_id: str):
        """Get a specific payment by ID."""
        return PaymentRepository.get_by_id(payment_id)

    @staticmethod
    def get_case_payments(case_id: str, user_id: str, user_role: str):
        """
        Get payments for a case (requires authorization).
        
        Args:
            case_id: The case ID
            user_id: The user ID requesting payments
            user_role: The role of the user
            
        Returns:
            List[Payment]: List of payments
            
        Raises:
            ValueError: If unauthorized
        """
        # Import locally to avoid circular imports
        from ..services.case_assignment_service import CaseAssignmentService
        
        # Check if user can access the case
        if not CaseAssignmentService.can_user_access_case(user_id, case_id, user_role):
            raise ValueError("Unauthorized to access this case")
        
        return PaymentRepository.get_payments_for_case(case_id)

    @staticmethod
    def confirm_payment(stripe_payment_intent_id: str):
        """
        Confirm a payment via Stripe webhook.
        
        Args:
            stripe_payment_intent_id: The Stripe payment intent ID
            
        Returns:
            Payment: The updated payment record
            
        Raises:
            ValueError: If payment not found
        """
        payment = PaymentRepository.get_by_stripe_payment_intent_id(stripe_payment_intent_id)
        if not payment:
            raise ValueError("Payment not found")
        
        # Update payment status
        PaymentRepository.update_status(payment.id, "completed")
        
        # Create notification for payment completion
        from ..services.notification_service import NotificationService
        NotificationService.create_payment_notification(
            user_id=payment.user_id,
            payment_id=payment.id,
            status="completed",
            amount_cents=payment.amount_cents
        )
        
        return payment

    @staticmethod
    def fail_payment(stripe_payment_intent_id: str):
        """
        Mark a payment as failed via Stripe webhook.
        
        Args:
            stripe_payment_intent_id: The Stripe payment intent ID
            
        Returns:
            Payment: The updated payment record
            
        Raises:
            ValueError: If payment not found
        """
        payment = PaymentRepository.get_by_stripe_payment_intent_id(stripe_payment_intent_id)
        if not payment:
            raise ValueError("Payment not found")
        
        # Update payment status
        PaymentRepository.update_status(payment.id, "failed")
        
        # Create notification for payment failure
        from ..services.notification_service import NotificationService
        NotificationService.create_payment_notification(
            user_id=payment.user_id,
            payment_id=payment.id,
            status="failed",
            amount_cents=payment.amount_cents
        )
        
        return payment

    @staticmethod
    def refund_payment(payment_id: str, amount_cents: Optional[int] = None):
        """
        Refund a payment.
        
        Args:
            payment_id: The payment ID to refund
            amount_cents: Amount to refund in cents (None for full refund)
            
        Returns:
            Payment: The updated payment record
            
        Raises:
            ValueError: If payment not found or already refunded
        """
        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status != "completed":
            raise ValueError("Only completed payments can be refunded")
        
        if payment.status == "refunded":
            raise ValueError("Payment already refunded")
        
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            # Create refund
            refund_params = {"payment_intent": payment.stripe_payment_intent_id}
            if amount_cents:
                refund_params["amount"] = amount_cents
            
            refund = stripe.Refund.create(**refund_params)
            
            # Update payment status
            PaymentRepository.update_status(payment.id, "refunded", refund.id)
            
        except Exception as e:
            raise ValueError(f"Refund failed: {str(e)}")
        
        return payment
