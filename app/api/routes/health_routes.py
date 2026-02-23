"""Health check for load balancer and ops."""
from flask import Blueprint, current_app
from sqlalchemy import text
from app.core.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Return 200 and optional db status. No auth required."""
    db_status = "ok"
    if not current_app.config.get("TESTING"):
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = str(e)
    return {"status": "ok", "db": db_status}, 200
