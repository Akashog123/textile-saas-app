import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from models.model import db, Shop, User, Notification
from utils.auth_utils import token_required
from utils.validation import validate_file_upload
from services.ai_service import generate_ai_caption, analyze_fabric_inquiry

inquiry_bp = Blueprint("inquiry", __name__, url_prefix="/api/v1/inquiry")

# Configuration
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}
UPLOAD_SUBFOLDER = "inquiries"


# Helpers
def allowed_file(filename):
    """Validate allowed file types."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_inquiry_file(file):
    """Save uploaded file securely to uploads directory."""
    if not file or not allowed_file(file.filename):
        return None

    upload_root = current_app.config.get("UPLOAD_FOLDER", "uploads")
    upload_dir = os.path.join(upload_root, UPLOAD_SUBFOLDER)
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{timestamp}_{file.filename}")
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return filepath


# POST: Submit + Analyze Fabric Inquiry (AI + Save)
@inquiry_bp.route("/submit", methods=["POST"])
@token_required
def submit_inquiry(current_user):
    """
    Allow shop owners to submit a fabric inquiry to multiple distributors with optional image.
    Images are sent directly to distributors without AI analysis.
    """
    try:
        print("[Info] Received form data:", request.form)
        print("[Info] Received files:", request.files)

        data = request.form or request.get_json(silent=True) or {}

        distributor_ids = data.get("distributor_ids")
        message = data.get("message", "").strip()
        file = request.files.get("image")  # Changed from 'file' to 'image'
        
        user_id = current_user.get("id")
        username = current_user.get("username", "User")

        # Validate required fields
        if not distributor_ids:
            return jsonify({"status": "error", "message": "distributor_ids is required"}), 400

        # Parse distributor IDs
        try:
            import json
            distributor_ids = json.loads(distributor_ids)
            if not isinstance(distributor_ids, list) or len(distributor_ids) == 0:
                raise ValueError("Invalid distributor_ids format")
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({"status": "error", "message": "Invalid distributor_ids format"}), 400

        # Validate distributors
        distributors = User.query.filter(
            User.id.in_(distributor_ids),
            User.role == "distributor",
            User.approved == True
        ).all()

        if len(distributors) != len(distributor_ids):
            return jsonify({"status": "error", "message": "Some distributors are invalid or not approved"}), 404
        
        # Validate file if provided
        if file:
            is_valid, file_message = validate_file_upload(file, ['.png', '.jpg', '.jpeg', '.gif', '.pdf'], max_size_mb=10)
            if not is_valid:
                return jsonify({"status": "error", "message": file_message}), 400

        # Save uploaded file (if any)
        file_path = save_inquiry_file(file)

        # Create notifications for each distributor
        notifications_created = []
        for distributor in distributors:
            notification = Notification(
                user_id=distributor.id,
                message=f"Inquiry from {username}: {message or 'No message provided'}",
                link=file_path.replace("\\", "/") if file_path else None,
                is_read=False
            )
            db.session.add(notification)
            notifications_created.append({
                "distributor_id": distributor.id,
                "distributor_name": distributor.full_name
            })

        db.session.commit()

        # Return structured response
        return jsonify({
            "status": "success",
            "message": f"Inquiry sent to {len(distributors)} distributor(s)",
            "notifications_created": notifications_created,
            "file_uploaded": bool(file_path),
            "file_path": file_path.replace("\\", "/") if file_path else None
        })

    except Exception as e:
        print("Inquiry submission error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to submit inquiry",
            "error": str(e)
        }), 500


# GET: Inquiry History for Shop/User
@inquiry_bp.route("/history", methods=["GET"])
@token_required
def inquiry_history(current_user):
    """Fetch all inquiries made by or received by the current authenticated user."""
    try:
        print("[Info] Fetching history for user:", current_user)
        
        user_id = current_user.get("id")
        role = current_user.get("role", "customer").lower()

        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        if role == "shop_owner":
            # For shop owners: get notifications they sent (inquiries they made)
            messages = Notification.query.filter(
                Notification.message.ilike(f"%Inquiry from%")
            ).order_by(Notification.created_at.desc()).all()
        elif role == "distributor":
            # For distributors: get notifications they received
            messages = Notification.query.filter_by(
                user_id=user_id
            ).order_by(Notification.created_at.desc()).all()
        else:
            # For customers/other roles: get their own notifications
            messages = Notification.query.filter_by(
                user_id=user_id
            ).order_by(Notification.created_at.desc()).all()

        history = [{
            "id": n.id,
            "message": n.message,
            "file": getattr(n, "link", None),
            "date": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "read": n.is_read
        } for n in messages]

        return jsonify({
            "status": "success",
            "count": len(history),
            "history": history
        }), 200

    except Exception as e:
        print("Inquiry history fetch error:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to fetch inquiry history",
            "error": str(e)
        }), 500
