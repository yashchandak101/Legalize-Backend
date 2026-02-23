# app/core/permissions.py
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify, request
from app.models.user import User
from app.domain.enums import RoleEnum

def role_required(required_role: RoleEnum):
    """
    Flask decorator to enforce role-based access.
    Example:
        @role_required(RoleEnum.LAWYER)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            if user.role != required_role.value:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator