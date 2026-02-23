from flask import Blueprint, jsonify

user_bp = Blueprint("users", __name__)

@user_bp.route("/", methods=["GET"])
def get_users():
    return jsonify({"message": "Users endpoint working"})