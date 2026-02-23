from flask import Blueprint, request, jsonify
from ...services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        user = AuthService.register(
            email=data["email"],
            password=data["password"],
            role=data.get("role", "user"),
        )
        return jsonify({"id": user.id, "email": user.email}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        result = AuthService.login(
            email=data["email"],
            password=data["password"],
        )
        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid credentials"}), 401