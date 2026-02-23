from ..models.notification import Notification
from ..core.extensions import db


class NotificationRepository:

    @staticmethod
    def create(notification: Notification):
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_by_id(notification_id: str):
        return Notification.query.get(notification_id)

    @staticmethod
    def get_user_notifications(user_id: str, unread_only: bool = False, limit: int = 50, offset: int = 0):
        """Get notifications for a user with pagination."""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter(Notification.read_at.is_(None))
        
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_unread_count(user_id: str):
        """Get count of unread notifications for a user."""
        return Notification.query.filter_by(user_id=user_id, read_at=None).count()

    @staticmethod
    def mark_as_read(notification_id: str):
        """Mark a notification as read."""
        notification = Notification.query.get(notification_id)
        if notification and not notification.read_at:
            notification.mark_as_read()
        return notification

    @staticmethod
    def mark_all_as_read(user_id: str):
        """Mark all notifications as read for a user."""
        from datetime import datetime, timezone
        
        unread_notifications = Notification.query.filter_by(
            user_id=user_id, 
            read_at=None
        ).all()
        
        for notification in unread_notifications:
            notification.read_at = datetime.now(timezone.utc)
        
        db.session.commit()
        return len(unread_notifications)

    @staticmethod
    def delete(notification: Notification):
        db.session.delete(notification)
        db.session.commit()

    @staticmethod
    def create_notification(user_id: str, kind: str, title: str, body: str, payload: dict = None):
        """Convenience method to create a notification."""
        notification = Notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            payload=payload
        )
        return NotificationRepository.create(notification)
