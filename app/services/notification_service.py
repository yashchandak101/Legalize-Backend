from typing import List, Optional, Dict, Any
from ..models.notification import Notification
from ..repositories.notification_repository import NotificationRepository


class NotificationService:

    # Notification kinds
    KIND_CASE_ASSIGNED = "case_assigned"
    KIND_CASE_UPDATED = "case_updated"
    KIND_APPOINTMENT_CONFIRMED = "appointment_confirmed"
    KIND_APPOINTMENT_CANCELLED = "appointment_cancelled"
    KIND_APPOINTMENT_REMINDER = "appointment_reminder"
    KIND_PAYMENT_RECEIVED = "payment_received"
    KIND_PAYMENT_FAILED = "payment_failed"
    KIND_DOCUMENT_UPLOADED = "document_uploaded"
    KIND_COMMENT_ADDED = "comment_added"

    @staticmethod
    def create_notification(user_id: str, kind: str, title: str, body: str, 
                           payload: Dict[str, Any] = None) -> Notification:
        """
        Create a notification for a user.
        
        Args:
            user_id: The user ID to create notification for
            kind: The notification kind/type
            title: The notification title
            body: The notification body
            payload: Optional additional data
            
        Returns:
            Notification: The created notification
        """
        return NotificationRepository.create_notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            payload=payload
        )

    @staticmethod
    def get_user_notifications(user_id: str, unread_only: bool = False, 
                               page: int = 1, per_page: int = 20) -> List[Notification]:
        """
        Get notifications for a user with pagination.
        
        Args:
            user_id: The user ID
            unread_only: Whether to get only unread notifications
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            List[Notification]: List of notifications
        """
        offset = (page - 1) * per_page
        return NotificationRepository.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=per_page,
            offset=offset
        )

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications for a user."""
        return NotificationRepository.get_unread_count(user_id)

    @staticmethod
    def get_notification_by_id(notification_id: str):
        """Get a specific notification by ID."""
        return NotificationRepository.get_by_id(notification_id)

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> Optional[Notification]:
        """
        Mark a notification as read (user can only mark their own).
        
        Args:
            notification_id: The notification ID
            user_id: The user ID marking as read
            
        Returns:
            Notification: The updated notification or None if not found
            
        Raises:
            ValueError: If notification doesn't belong to user
        """
        notification = NotificationRepository.get_by_id(notification_id)
        if not notification:
            return None
        
        if notification.user_id != user_id:
            raise ValueError("Unauthorized to mark notification as read")
        
        return NotificationRepository.mark_as_read(notification_id)

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            int: Number of notifications marked as read
        """
        return NotificationRepository.mark_all_as_read(user_id)

    @staticmethod
    def create_case_assigned_notification(case_id: str, lawyer_id: str, client_id: str):
        """Create notification when a case is assigned to a lawyer."""
        # Notify the lawyer
        NotificationService.create_notification(
            user_id=lawyer_id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="New Case Assignment",
            body="You have been assigned to a new case.",
            payload={"case_id": case_id}
        )

        # Notify the client
        NotificationService.create_notification(
            user_id=client_id,
            kind=NotificationService.KIND_CASE_ASSIGNED,
            title="Lawyer Assigned to Your Case",
            body="A lawyer has been assigned to your case.",
            payload={"case_id": case_id}
        )

    @staticmethod
    def create_payment_notification(user_id: str, payment_id: str, status: str, amount_cents: int):
        """Create notification for payment status change."""
        if status == "completed":
            kind = NotificationService.KIND_PAYMENT_RECEIVED
            title = "Payment Received"
            body = f"Your payment of ${amount_cents / 100:.2f} was successful."
        elif status == "failed":
            kind = NotificationService.KIND_PAYMENT_FAILED
            title = "Payment Failed"
            body = f"Your payment of ${amount_cents / 100:.2f} failed. Please try again."
        else:
            return  # Don't create notification for other statuses
        
        NotificationService.create_notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            payload={"payment_id": payment_id, "amount_cents": amount_cents}
        )

    @staticmethod
    def create_appointment_notification(user_id: str, appointment_id: str, status: str):
        """Create notification for appointment status changes."""
        if status == "confirmed":
            kind = NotificationService.KIND_APPOINTMENT_CONFIRMED
            title = "Appointment Confirmed"
            body = "Your appointment has been confirmed."
        elif status == "cancelled":
            kind = NotificationService.KIND_APPOINTMENT_CANCELLED
            title = "Appointment Cancelled"
            body = "Your appointment has been cancelled."
        else:
            return  # Don't create notification for other statuses
        
        NotificationService.create_notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            payload={"appointment_id": appointment_id}
        )

    @staticmethod
    def create_comment_notification(user_id: str, case_id: str, comment_id: str, commenter_name: str):
        """Create notification when a comment is added to a user's case."""
        NotificationService.create_notification(
            user_id=user_id,
            kind=NotificationService.KIND_COMMENT_ADDED,
            title="New Comment on Your Case",
            body=f"{commenter_name} added a comment to your case.",
            payload={"case_id": case_id, "comment_id": comment_id}
        )

    @staticmethod
    def create_document_notification(user_id: str, case_id: str, document_id: str, filename: str):
        """Create notification when a document is uploaded to a user's case."""
        NotificationService.create_notification(
            user_id=user_id,
            kind=NotificationService.KIND_DOCUMENT_UPLOADED,
            title="Document Uploaded",
            body=f"A new document '{filename}' was uploaded to your case.",
            payload={"case_id": case_id, "document_id": document_id}
        )