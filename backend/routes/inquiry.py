import os
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from models.model import db, Shop, User, Notification, Inquiry, InquiryRecipient
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


# POST: Submit Inquiry (Story 4)
@inquiry_bp.route("/submit", methods=["POST"])
@token_required
def submit_inquiry(current_user):
    """
    Allow shop owners to submit a fabric inquiry to multiple distributors.
    Saves to Inquiry and InquiryRecipient tables.
    """
    try:
        # print("[Info] Received form data:", request.form)
        
        data = request.form or request.get_json(silent=True) or {}

        distributor_ids = data.get("distributor_ids")
        message = data.get("message", "").strip()
        file = request.files.get("image")
        
        user_id = current_user.get("id")
        
        # Validate required fields
        if not distributor_ids:
            return jsonify({"status": "error", "message": "distributor_ids is required"}), 400

        # Parse distributor IDs
        try:
            if isinstance(distributor_ids, str):
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
        file_path = None
        if file:
            is_valid, file_message = validate_file_upload(file, ['.png', '.jpg', '.jpeg', '.gif', '.pdf'], max_size_mb=10)
            if not is_valid:
                return jsonify({"status": "error", "message": file_message}), 400
            file_path = save_inquiry_file(file)

        # Create Inquiry Record
        inquiry = Inquiry(
            sender_id=user_id,
            message=message,
            image_url=file_path.replace("\\", "/") if file_path else None
        )
        db.session.add(inquiry)
        db.session.flush() # Get ID

        # Create Recipients and Notifications
        notifications_created = []
        for distributor in distributors:
            # 1. Inquiry Recipient Record
            recipient = InquiryRecipient(
                inquiry_id=inquiry.id,
                recipient_id=distributor.id,
                status="pending"
            )
            db.session.add(recipient)
            
            # 2. Notification (Legacy/Alert)
            notification = Notification(
                user_id=distributor.id,
                message=f"New Inquiry from {current_user.get('username')}: {message[:50]}...",
                link=f"/inquiries/{inquiry.id}", # Deep link to inquiry view
                is_read=False
            )
            db.session.add(notification)
            
            notifications_created.append({
                "distributor_id": distributor.id,
                "distributor_name": distributor.full_name
            })

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Inquiry sent to {len(distributors)} distributor(s)",
            "inquiry_id": inquiry.id,
            "notifications_created": notifications_created,
            "file_path": inquiry.image_url
        })

    except Exception as e:
        print("Inquiry submission error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to submit inquiry",
            "error": str(e)
        }), 500


# GET: Inquiry History
@inquiry_bp.route("/history", methods=["GET"])
@token_required
def inquiry_history(current_user):
    """Fetch inquiry history based on user role."""
    try:
        user_id = current_user.get("id")
        role = current_user.get("role", "customer").lower()

        history = []

        if role == "shop_owner" or role == "shop_manager":
            # Sent Inquiries
            inquiries = Inquiry.query.filter_by(sender_id=user_id).order_by(Inquiry.created_at.desc()).all()
            
            for ing in inquiries:
                # Get recipient names
                recipients = [r.recipient.full_name for r in ing.recipients]
                
                history.append({
                    "id": ing.id,
                    "message": ing.message,
                    "image_url": ing.image_url,
                    "created_at": ing.created_at.isoformat(),
                    "recipients": recipients,
                    "status": "sent" # Simplified for sender
                })
                
        elif role == "distributor":
            # Received Inquiries
            received = InquiryRecipient.query.filter_by(recipient_id=user_id).order_by(InquiryRecipient.created_at.desc()).all()
            
            for r in received:
                ing = r.inquiry
                history.append({
                    "id": ing.id,
                    "message": ing.message,
                    "image_url": ing.image_url,
                    "created_at": ing.created_at.isoformat(),
                    "sender_name": ing.sender.full_name,
                    "shop_name": ing.sender.shops.first().name if ing.sender.shops.first() else "Unknown Shop",
                    "status": r.status,
                    "read_at": r.read_at.isoformat() if r.read_at else None
                })
        
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
