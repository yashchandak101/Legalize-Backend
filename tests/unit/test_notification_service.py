import pytest
from app.core.extensions import db
from app.services.notification_service import NotificationService
from app.services.auth_service import AuthService
from app.domain.enums import RoleEnum
from app.models.notification import Notification
from app.models.user import User


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
def sample_lawyer_user():
    """A lawyer user for testing."""
    user = User(
        email="lawyer@test.example",
        password="hashed",
        role=RoleEnum.LAWYER.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


class TestNotificationService:
    """Test cases for NotificationService."""

    def test_create_notification_success(self, sample_client_user):
        """Test successful notification creation."""
        user = sample_client_user
        
        notification = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Test Notification",
            body="This is a test notification",
            payload={"case_id": "test_case_id"}
        )
        
        assert notification is not None
        assert notification.user_id == user.id
        assert notification.kind == NotificationService.KIND_CASE_ASSIGNED
        assert notification.title == "Test Notification"
        assert notification.body == "This is a test notification"
        assert notification.payload == {"case_id": "test_case_id"}
        assert notification.read_at is None

    def test_get_user_notifications(self, sample_client_user):
        """Test getting user notifications."""
        user = sample_client_user
        
        # Create multiple notifications
        notification1 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Notification 1",
            body="First notification"
        )
        
        notification2 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_PAYMENT_RECEIVED,
            title="Notification 2",
            body="Second notification"
        )
        
        # Get all notifications
        notifications = NotificationService.get_user_notifications(user_id=user.id)
        
        assert len(notifications) == 2
        # Should be ordered by created_at desc
        assert notifications[0].id == notification2.id
        assert notifications[1].id == notification1.id

    def test_get_unread_notifications_only(self, sample_client_user):
        """Test getting only unread notifications."""
        user = sample_client_user
        
        # Create notifications
        notification1 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Notification 1",
            body="First notification"
        )
        
        notification2 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_PAYMENT_RECEIVED,
            title="Notification 2",
            body="Second notification"
        )
        
        # Mark one as read
        NotificationService.mark_as_read(notification1.id, user.id)
        
        # Get only unread notifications
        unread_notifications = NotificationService.get_user_notifications(
            user_id=user.id,
            unread_only=True
        )
        
        assert len(unread_notifications) == 1
        assert unread_notifications[0].id == notification2.id

    def test_get_unread_count(self, sample_client_user):
        """Test getting unread count."""
        user = sample_client_user
        
        # Create notifications
        notification1 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Notification 1",
            body="First notification"
        )
        
        notification2 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_PAYMENT_RECEIVED,
            title="Notification 2",
            body="Second notification"
        )
        
        # Initially all are unread
        count = NotificationService.get_unread_count(user.id)
        assert count == 2
        
        # Mark one as read
        NotificationService.mark_as_read(notification1.id, user.id)
        
        # Now only one is unread
        count = NotificationService.get_unread_count(user.id)
        assert count == 1

    def test_mark_as_read_success(self, sample_client_user):
        """Test marking notification as read."""
        user = sample_client_user
        
        notification = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Test Notification",
            body="Test body"
        )
        
        # Initially unread
        assert notification.read_at is None
        
        # Mark as read
        updated_notification = NotificationService.mark_as_read(notification.id, user.id)
        
        assert updated_notification is not None
        assert updated_notification.read_at is not None
        assert updated_notification.is_read() is True

    def test_mark_as_read_unauthorized_fails(self, sample_client_user, sample_lawyer_user):
        """Test that users cannot mark others' notifications as read."""
        client = sample_client_user
        lawyer = sample_lawyer_user
        
        # Create notification for client
        notification = NotificationService.create_notification(
            user_id=client.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Client Notification",
            body="For client only"
        )
        
        # Lawyer tries to mark client's notification as read
        with pytest.raises(ValueError, match="Unauthorized to mark notification as read"):
            NotificationService.mark_as_read(notification.id, lawyer.id)

    def test_mark_as_read_not_found(self, sample_client_user):
        """Test marking non-existent notification as read."""
        user = sample_client_user
        
        result = NotificationService.mark_as_read("non_existent_id", user.id)
        assert result is None

    def test_mark_all_as_read(self, sample_client_user):
        """Test marking all notifications as read."""
        user = sample_client_user
        
        # Create multiple notifications
        notification1 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Notification 1",
            body="First notification"
        )
        
        notification2 = NotificationService.create_notification(
            user_id=user.id,
            kind=NotificationService.KIND_PAYMENT_RECEIVED,
            title="Notification 2",
            body="Second notification"
        )
        
        # Mark all as read
        marked_count = NotificationService.mark_all_as_read(user.id)
        
        assert marked_count == 2
        
        # Verify all are read
        count = NotificationService.get_unread_count(user.id)
        assert count == 0

    def test_create_case_assigned_notification(self, sample_client_user, sample_lawyer_user):
        """Test creating case assignment notifications."""
        client = sample_client_user
        lawyer = sample_lawyer_user
        case_id = "test_case_id"
        
        # Create notifications
        NotificationService.create_case_assigned_notification(
            case_id=case_id,
            lawyer_id=lawyer.id,
            client_id=client.id
        )
        
        # Check both users received notifications
        lawyer_notifications = NotificationService.get_user_notifications(lawyer.id)
        client_notifications = NotificationService.get_user_notifications(client.id)
        
        assert len(lawyer_notifications) == 1
        assert lawyer_notifications[0].kind == NotificationService.KIND_CASE_ASSIGNED
        assert lawyer_notifications[0].title == "New Case Assignment"
        
        assert len(client_notifications) == 1
        assert client_notifications[0].kind == NotificationService.KIND_CASE_ASSIGNED
        assert client_notifications[0].title == "Lawyer Assigned to Your Case"

    def test_create_payment_notification_completed(self, sample_client_user):
        """Test creating payment completed notification."""
        user = sample_client_user
        payment_id = "test_payment_id"
        amount_cents = 5000
        
        NotificationService.create_payment_notification(
            user_id=user.id,
            payment_id=payment_id,
            status="completed",
            amount_cents=amount_cents
        )
        
        notifications = NotificationService.get_user_notifications(user.id)
        assert len(notifications) == 1
        assert notifications[0].kind == NotificationService.KIND_PAYMENT_RECEIVED
        assert notifications[0].title == "Payment Received"
        assert "50.00" in notifications[0].body

    def test_create_payment_notification_failed(self, sample_client_user):
        """Test creating payment failed notification."""
        user = sample_client_user
        payment_id = "test_payment_id"
        amount_cents = 5000
        
        NotificationService.create_payment_notification(
            user_id=user.id,
            payment_id=payment_id,
            status="failed",
            amount_cents=amount_cents
        )
        
        notifications = NotificationService.get_user_notifications(user.id)
        assert len(notifications) == 1
        assert notifications[0].kind == NotificationService.KIND_PAYMENT_FAILED
        assert notifications[0].title == "Payment Failed"
        assert "50.00" in notifications[0].body

    def test_create_payment_notification_ignored_status(self, sample_client_user):
        """Test that non-payment statuses don't create notifications."""
        user = sample_client_user
        payment_id = "test_payment_id"
        amount_cents = 5000
        
        # Try with a status that shouldn't create notifications
        NotificationService.create_payment_notification(
            user_id=user.id,
            payment_id=payment_id,
            status="pending",  # This should not create a notification
            amount_cents=amount_cents
        )
        
        notifications = NotificationService.get_user_notifications(user.id)
        assert len(notifications) == 0

    def test_create_comment_notification(self, sample_client_user):
        """Test creating comment notification."""
        user = sample_client_user
        case_id = "test_case_id"
        comment_id = "test_comment_id"
        commenter_name = "John Doe"
        
        NotificationService.create_comment_notification(
            user_id=user.id,
            case_id=case_id,
            comment_id=comment_id,
            commenter_name=commenter_name
        )
        
        notifications = NotificationService.get_user_notifications(user.id)
        assert len(notifications) == 1
        assert notifications[0].kind == NotificationService.KIND_COMMENT_ADDED
        assert notifications[0].title == "New Comment on Your Case"
        assert commenter_name in notifications[0].body

    def test_create_document_notification(self, sample_client_user):
        """Test creating document notification."""
        user = sample_client_user
        case_id = "test_case_id"
        document_id = "test_document_id"
        filename = "test_document.pdf"
        
        NotificationService.create_document_notification(
            user_id=user.id,
            case_id=case_id,
            document_id=document_id,
            filename=filename
        )
        
        notifications = NotificationService.get_user_notifications(user.id)
        assert len(notifications) == 1
        assert notifications[0].kind == NotificationService.KIND_DOCUMENT_UPLOADED
        assert notifications[0].title == "Document Uploaded"
        assert filename in notifications[0].body
