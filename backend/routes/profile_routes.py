# routes/profile.py

from flask import Blueprint, request, jsonify
from models.model import db, User
from routes.auth_routes import token_required

profile_bp = Blueprint("profile", __name__)

# ───────────────────────────────────────────────
# 👤 Fetch Current User Profile
# ───────────────────────────────────────────────
@profile_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """
    Fetch the logged-in user's profile details.
    """
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        profile_data = {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "contact": user.contact or "",
            "address": user.address or "",
            "city": user.city or "",
            "state": user.state or "",
            "pincode": user.pincode or "",
            "role": user.role,
            "approved": user.approved,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

        return jsonify({
            "status": "success",
            "message": "Profile fetched successfully.",
            "profile": profile_data
        }), 200

    except Exception as e:
        print("[Error - Fetch Profile]", e)
        return jsonify({
            "status": "error",
            "message": "Internal server error.",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# ✏️ Update User Profile
# ───────────────────────────────────────────────
@profile_bp.route("/profile/update", methods=["PUT"])
@token_required
def update_profile(current_user):
    """
    Update current user's profile fields dynamically.
    Only allows editing of basic info (not role or approval).
    """
    try:
        data = request.get_json() or {}
        user = User.query.get(current_user.id)

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        editable_fields = [
            "full_name", "username", "email", "contact",
            "address", "city", "state", "pincode"
        ]

        updated_fields = 0
        for field in editable_fields:
            if field in data and hasattr(user, field):
                setattr(user, field, data[field])
                updated_fields += 1

        if updated_fields == 0:
            return jsonify({"status": "error", "message": "No valid fields to update."}), 400

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Profile updated successfully!",
            "updated_fields": updated_fields
        }), 200

    except Exception as e:
        print("[Error - Update Profile]", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to update profile.",
            "error": str(e)
        }), 500
