from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

from app.services.payment_service import PaymentService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be payment_bp
payment_bp = Blueprint("payment_bp", __name__)


# ---------------------------------------
# Create Payment Intent
# ---------------------------------------
@payment_bp.route("/cases/<case_id>/payments", methods=["POST"])
@jwt_required()
def create_payment_intent(case_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    amount_cents = data.get("amount_cents")
    description = data.get("description", "")
    
    if not amount_cents:
        return api_error("Amount in cents is required", 400, code="VALIDATION_ERROR")
    
    if amount_cents <= 0:
        return api_error("Amount must be greater than 0", 400, code="VALIDATION_ERROR")
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        payment = PaymentService.create_payment_intent(
            case_id=case_id,
            user_id=user_id,
            amount_cents=amount_cents,
            description=description,
            actor_role=user.role
        )
        return jsonify(payment.to_dict()), 201
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get User Payments
# ---------------------------------------
@payment_bp.route("/payments", methods=["GET"])
@jwt_required()
def get_user_payments():
    user_id = get_jwt_identity()
    
    try:
        payments = PaymentService.get_user_payments(user_id)
        return jsonify([payment.to_dict() for payment in payments]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Case Payments
# ---------------------------------------
@payment_bp.route("/cases/<case_id>/payments", methods=["GET"])
@jwt_required()
def get_case_payments(case_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        payments = PaymentService.get_case_payments(
            case_id=case_id,
            user_id=user_id,
            user_role=user.role
        )
        return jsonify([payment.to_dict() for payment in payments]), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Single Payment
# ---------------------------------------
@payment_bp.route("/payments/<payment_id>", methods=["GET"])
@jwt_required()
def get_payment(payment_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        payment = PaymentService.get_payment_by_id(payment_id)
        if not payment:
            return api_error("Payment not found", 404, code="NOT_FOUND")
        
        # Check if user owns the payment
        if payment.user_id != user_id and user.role != "admin":
            return api_error("Unauthorized", 403, code="FORBIDDEN")
        
        return jsonify(payment.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Refund Payment
# ---------------------------------------
@payment_bp.route("/payments/<payment_id>/refund", methods=["POST"])
@jwt_required()
def refund_payment(payment_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return api_error("Invalid JSON", 400)
    
    amount_cents = data.get("amount_cents")  # Optional, for partial refunds
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        payment = PaymentService.get_payment_by_id(payment_id)
        if not payment:
            return api_error("Payment not found", 404, code="NOT_FOUND")
        
        # Check if user owns the payment or is admin
        if payment.user_id != user_id and user.role != "admin":
            return api_error("Unauthorized", 403, code="FORBIDDEN")
        
        refunded_payment = PaymentService.refund_payment(
            payment_id=payment_id,
            amount_cents=amount_cents
        )
        return jsonify(refunded_payment.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Stripe Webhook
# ---------------------------------------
@payment_bp.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhooks for payment events."""
    import stripe
    
    # Get the webhook signature
    signature = request.headers.get('stripe-signature')
    if not signature:
        return api_error("Missing Stripe signature", 400)
    
    # Get the webhook secret key
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        return api_error("Webhook secret not configured", 500)
    
    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            payload=request.data,
            sig_header=signature,
            secret=webhook_secret
        )
    except ValueError as e:
        return api_error(f"Invalid webhook signature: {str(e)}", 400)
    except stripe.error.SignatureVerificationError as e:
        return api_error(f"Webhook signature verification failed: {str(e)}", 400)
    
    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        try:
            payment = PaymentService.confirm_payment(payment_intent.id)
            print(f"Payment confirmed: {payment.id}")
        except ValueError as e:
            print(f"Error confirming payment: {str(e)}")
            return api_error(str(e), 400)
    
    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        try:
            payment = PaymentService.fail_payment(payment_intent.id)
            print(f"Payment failed: {payment.id}")
        except ValueError as e:
            print(f"Error failing payment: {str(e)}")
            return api_error(str(e), 400)
    
    else:
        print(f"Unhandled webhook event type: {event.type}")
    
    return jsonify({"status": "received"}), 200
