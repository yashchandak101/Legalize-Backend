from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.notification_service import NotificationService
from app.services.auth_service import AuthService
from app.core.api_errors import api_error

# IMPORTANT: variable name must be notification_bp
notification_bp = Blueprint("notification_bp", __name__)


# ---------------------------------------
# Get User Notifications
# ---------------------------------------
@notification_bp.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    
    # Get query parameters
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)  # Max 100 per page
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        notifications = NotificationService.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            page=page,
            per_page=per_page
        )
        return jsonify([notification.to_dict() for notification in notifications]), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Unread Count
# ---------------------------------------
@notification_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def get_unread_count():
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        count = NotificationService.get_unread_count(user_id)
        return jsonify({"unread_count": count}), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Mark Notification as Read
# ---------------------------------------
@notification_bp.route("/<notification_id>/read", methods=["PATCH"])
@jwt_required()
def mark_as_read(notification_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        notification = NotificationService.mark_as_read(
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not notification:
            return api_error("Notification not found", 404, code="NOT_FOUND")
        
        return jsonify(notification.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Mark All as Read
# ---------------------------------------
@notification_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_as_read():
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        count = NotificationService.mark_all_as_read(user_id)
        return jsonify({"marked_as_read": count}), 200
        
    except Exception as e:
        return api_error("Internal server error", 500)


# ---------------------------------------
# Get Single Notification
# ---------------------------------------
@notification_bp.route("/<notification_id>", methods=["GET"])
@jwt_required()
def get_notification(notification_id):
    user_id = get_jwt_identity()
    
    # Get user to verify role
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return api_error("User not found", 404, code="NOT_FOUND")
    
    try:
        notification = NotificationService.get_notification_by_id(notification_id)
        if not notification:
            return api_error("Notification not found", 404, code="NOT_FOUND")
        
        # Check if user owns the notification
        if notification.user_id != user_id and user.role != "admin":
            return api_error("Unauthorized", 403, code="FORBIDDEN")
        
        return jsonify(notification.to_dict()), 200
        
    except ValueError as e:
        return api_error(str(e), 403)
    except Exception as e:
        return api_error("Internal server error", 500)
