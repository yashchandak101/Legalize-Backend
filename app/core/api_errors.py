"""
Standard API error responses.
All API errors return { "error": "<message>", "code": "<optional>" }.
"""
from flask import jsonify
from typing import Optional


def api_error(message: str, status: int = 400, code: Optional[str] = None):
    """Return (jsonify(response), status) for consistent error shape."""
    body = {"error": message}
    if code:
        body["code"] = code
    return jsonify(body), status
