import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from models.model import db, Shop, User, Notification
from services.ai_service import generate_ai_caption, analyze_fabric_inquiry

inquiry_bp = Blueprint("inquiry", __name__, url_prefix="/api/v1/inquiry")

# ───────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}
UPLOAD_SUBFOLDER = "inquiries"


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────
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


# ───────────────────────────────────────────────
# 1️⃣ POST: Submit + Analyze Fabric Inquiry (AI + Save)
# ───────────────────────────────────────────────
@inquiry_bp.route("/submit", methods=["POST"])
def submit_inquiry():
    """
    Allow customers or shop owners to submit a fabric inquiry with optional image/file attachment.
    Automatically runs Gemini-based AI analysis on the uploaded fabric image.
    """
    try:
        print("🔹 Received form data:", request.form)
        print("🔹 Received files:", request.files)

        data = request.form or request.get_json(silent=True) or {}

        shop_id = data.get("shop_id")
        user_id = data.get("user_id")
        username = data.get("username", "Anonymous")
        message = data.get("message", "").strip()
        file = request.files.get("file")

        # Validate required fields
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        # Validate shop
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Invalid shop ID"}), 404

        # Save uploaded file (if any)
        file_path = save_inquiry_file(file)

        # Run AI-based fabric analysis (only if file uploaded)
        ai_result = None
        if file_path:
            ai_result = analyze_fabric_inquiry(file_path, message)
            print("🧠 AI Inquiry Result:", ai_result)
        else:
            ai_result = {"analysis": "No image uploaded, only text message received."}

        # Fallback acknowledgment if Gemini unavailable
        ai_ack = (
            ai_result.get("analysis") 
            if isinstance(ai_result, dict) and "analysis" in ai_result 
            else generate_ai_caption(shop.name, "Fabric Inquiry", 0)
        )

        # Save inquiry as a notification record
        notification = Notification(
            user_id=user_id,
            message=f"Inquiry to {shop.name}: {message or 'No message provided'}",
            link=file_path.replace("\\", "/") if file_path else None,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        # Return structured response
        return jsonify({
            "status": "success",
            "message": "Fabric inquiry analyzed and submitted successfully!",
            "details": {
                "shop": shop.name,
                "file_path": file_path.replace("\\", "/") if file_path else None,
                "ai_analysis": ai_result,
                "ai_acknowledgment": ai_ack,
                "submitted_by": username
            }
        }), 201

    except Exception as e:
        print("❌ Inquiry submission error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to submit inquiry",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# 2️⃣ GET: Inquiry History for Shop/User (No JWT)
# ───────────────────────────────────────────────
@inquiry_bp.route("/history", methods=["GET"])
def inquiry_history():
    """Fetch all inquiries (notifications) made by a given user or shop."""
    try:
        print("🔹 Incoming query params:", request.args)

        user_id = request.args.get("user_id")
        role = request.args.get("role", "user")

        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400

        # For shop owners → show inquiries related to their shop
        if role == "shop_owner":
            shop = Shop.query.filter_by(owner_id=user_id).first()
            if not shop:
                return jsonify({"status": "error", "message": "Shop not found"}), 404

            messages = Notification.query.filter(
                Notification.message.ilike(f"%{shop.name}%")
            ).order_by(Notification.created_at.desc()).all()
        else:
            # For regular users
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
        print("❌ Inquiry history fetch error:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to fetch inquiry history",
            "error": str(e)
        }), 500
