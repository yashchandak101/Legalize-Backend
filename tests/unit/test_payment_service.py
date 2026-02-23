import pytest
from app.core.extensions import db
from app.services.payment_service import PaymentService
from app.services.case_service import CaseService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.payment import Payment
from app.models.user import User
from app.models.case import Case


@pytest.fixture
def sample_case():
    """A sample case for testing."""
    # Create a case owner first
    case_owner = User(
        email="caseowner@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(case_owner)
    db.session.flush()
    
    return CaseService.create_case(
        user_id=case_owner.id,
        title="Test case",
        description="Description for test case",
    )


@pytest.fixture
def sample_client_user():
    """A client user for testing."""
    user = User(
        email="client@test.example",
        password="hashed",
        role=RoleEnum.USER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def sample_admin_user():
    """An admin user for testing."""
    user = User(
        email="admin@test.example",
        password="hashed",
        role=RoleEnum.ADMIN.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


class TestPaymentService:
    """Test cases for PaymentService."""

    def test_create_payment_intent_success(self, sample_case, sample_client_user):
        """Test successful payment intent creation."""
        case = sample_case
        client = sample_client_user
        
        # Mock Stripe to avoid actual API calls
        import stripe
        original_create = stripe.PaymentIntent.create
        
        def mock_create(**kwargs):
            class MockIntent:
                def __init__(self):
                    self.id = "pi_test_123"
                    self.client_secret = "pi_test_123_secret_test"
            return MockIntent()
        
        stripe.PaymentIntent.create = mock_create
        
        try:
            payment = PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=5000,  # $50.00
                description="Test payment",
                actor_role=client.role
            )
            
            assert payment is not None
            assert payment.case_id == case.id
            assert payment.user_id == client.id
            assert payment.amount_cents == 5000
            assert payment.status == "pending"
            assert payment.stripe_payment_intent_id == "pi_test_123"
            assert payment.stripe_client_secret == "pi_test_123_secret_test"
            
        finally:
            # Restore original method
            stripe.PaymentIntent.create = original_create

    def test_create_payment_intent_unauthorized_fails(self, sample_case, sample_client_user):
        """Test that unauthorized users cannot create payment intents."""
        case = sample_case
        client = sample_client_user
        
        # Create a different user who doesn't have access
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=other_user.id,
                amount_cents=5000,
                actor_role=other_user.role
            )

    def test_create_payment_intent_invalid_amount_fails(self, sample_case, sample_client_user):
        """Test that invalid amounts fail."""
        case = sample_case
        client = sample_client_user
        
        with pytest.raises(ValueError, match="Amount must be greater than 0"):
            PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=0,
                actor_role=client.role
            )

    def test_get_user_payments(self, sample_case, sample_client_user):
        """Test getting user payments."""
        case = sample_case
        client = sample_client_user
        
        # Mock Stripe
        import stripe
        original_create = stripe.PaymentIntent.create
        
        def mock_create(**kwargs):
            class MockIntent:
                def __init__(self):
                    self.id = "pi_test_123"
                    self.client_secret = "pi_test_123_secret_test"
            return MockIntent()
        
        stripe.PaymentIntent.create = mock_create
        
        try:
            # Create a payment
            payment = PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=5000,
                actor_role=client.role
            )
            
            # Get user payments
            payments = PaymentService.get_user_payments(client.id)
            
            assert len(payments) == 1
            assert payments[0].id == payment.id
            
        finally:
            stripe.PaymentIntent.create = original_create

    def test_get_case_payments_authorized(self, sample_case, sample_client_user):
        """Test getting case payments for authorized user."""
        case = sample_case
        client = sample_client_user
        
        # Mock Stripe
        import stripe
        original_create = stripe.PaymentIntent.create
        
        def mock_create(**kwargs):
            class MockIntent:
                def __init__(self):
                    self.id = "pi_test_123"
                    self.client_secret = "pi_test_123_secret_test"
            return MockIntent()
        
        stripe.PaymentIntent.create = mock_create
        
        try:
            # Create a payment
            payment = PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=5000,
                actor_role=client.role
            )
            
            # Get case payments
            payments = PaymentService.get_case_payments(
                case_id=case.id,
                user_id=client.id,
                user_role=client.role
            )
            
            assert len(payments) == 1
            assert payments[0].id == payment.id
            
        finally:
            stripe.PaymentIntent.create = original_create

    def test_get_case_payments_unauthorized_fails(self, sample_case, sample_client_user):
        """Test that unauthorized users cannot get case payments."""
        case = sample_case
        client = sample_client_user
        
        # Create a different user
        other_user = User(
            email="other@test.example",
            password="hashed",
            role=RoleEnum.USER.value,
        )
        db.session.add(other_user)
        db.session.flush()
        
        with pytest.raises(ValueError, match="Unauthorized to access this case"):
            PaymentService.get_case_payments(
                case_id=case.id,
                user_id=other_user.id,
                user_role=other_user.role
            )

    def test_confirm_payment_success(self, sample_case, sample_client_user):
        """Test successful payment confirmation."""
        case = sample_case
        client = sample_client_user
        
        # Mock Stripe for payment creation
        import stripe
        original_create = stripe.PaymentIntent.create
        
        def mock_create(**kwargs):
            class MockIntent:
                def __init__(self):
                    self.id = "pi_test_123"
                    self.client_secret = "pi_test_123_secret_test"
            return MockIntent()
        
        stripe.PaymentIntent.create = mock_create
        
        try:
            # Create a payment
            payment = PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=5000,
                actor_role=client.role
            )
            
            # Confirm payment
            confirmed_payment = PaymentService.confirm_payment(
                stripe_payment_intent_id="pi_test_123"
            )
            
            assert confirmed_payment is not None
            assert confirmed_payment.id == payment.id
            assert confirmed_payment.status == "completed"
            assert confirmed_payment.completed_at is not None
            
        finally:
            stripe.PaymentIntent.create = original_create

    def test_confirm_payment_not_found_fails(self):
        """Test that confirming non-existent payment fails."""
        with pytest.raises(ValueError, match="Payment not found"):
            PaymentService.confirm_payment("non_existent_intent_id")

    def test_fail_payment_success(self, sample_case, sample_client_user):
        """Test successful payment failure."""
        case = sample_case
        client = sample_client_user
        
        # Mock Stripe for payment creation
        import stripe
        original_create = stripe.PaymentIntent.create
        
        def mock_create(**kwargs):
            class MockIntent:
                def __init__(self):
                    self.id = "pi_test_123"
                    self.client_secret = "pi_test_123_secret_test"
            return MockIntent()
        
        stripe.PaymentIntent.create = mock_create
        
        try:
            # Create a payment
            payment = PaymentService.create_payment_intent(
                case_id=case.id,
                user_id=client.id,
                amount_cents=5000,
                actor_role=client.role
            )
            
            # Fail payment
            failed_payment = PaymentService.fail_payment(
                stripe_payment_intent_id="pi_test_123"
            )
            
            assert failed_payment is not None
            assert failed_payment.id == payment.id
            assert failed_payment.status == "failed"
            
        finally:
            stripe.PaymentIntent.create = original_create
