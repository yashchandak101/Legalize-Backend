"""
Structured logging: request_id, user_id, action.
Use for production-ready request/response logging.
"""
import logging
import uuid
from flask import g, request
from typing import Optional

logger = logging.getLogger("legalize")


def init_logging(app):
    """Register before_request and after_request to set request_id and log."""
    @app.before_request
    def set_request_id():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    @app.after_request
    def log_request(response):
        extra = {
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
        }
        user_id = None
        if hasattr(g, "user_id"):
            user_id = g.user_id
        else:
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
            except Exception:
                pass
        if user_id:
            extra["user_id"] = str(user_id)[:8] + "..." if len(str(user_id)) > 8 else str(user_id)
        logger.info("request", extra=extra)
        response.headers["X-Request-ID"] = extra["request_id"]
        return response
