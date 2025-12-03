import os
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from models.model import db, Shop, User, Notification, Inquiry, InquiryRecipient, InquiryMessage
from utils.auth_utils import token_required
from utils.validation import validate_file_upload

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


# ============================================================================
# CHAT / CONVERSATION ENDPOINTS
# ============================================================================

@inquiry_bp.route("/conversations", methods=["GET"])
@token_required
def get_conversations(current_user):
    """
    Get all conversation threads for the current user.
    For shop owners: conversations they started with distributors.
    For distributors: conversations from shop owners.
    """
    try:
        user_id = current_user.get("id")
        role = current_user.get("role", "").lower()
        conversations = []

        if role in ["shop_owner", "shop_manager"]:
            # Get all inquiries sent by this user, grouped by recipient
            inquiries = Inquiry.query.filter_by(sender_id=user_id).order_by(Inquiry.created_at.desc()).all()
            
            for inquiry in inquiries:
                for recipient in inquiry.recipients:
                    # Count unread messages (messages from distributor that shop owner hasn't read)
                    unread_count = InquiryMessage.query.filter(
                        InquiryMessage.inquiry_recipient_id == recipient.id,
                        InquiryMessage.sender_id != user_id,
                        InquiryMessage.is_read == False
                    ).count()
                    
                    # Get last message
                    last_message = InquiryMessage.query.filter_by(
                        inquiry_recipient_id=recipient.id
                    ).order_by(InquiryMessage.created_at.desc()).first()
                    
                    conversations.append({
                        "id": recipient.id,
                        "inquiry_id": inquiry.id,
                        "contact_id": recipient.recipient_id,
                        "contact_name": recipient.recipient.full_name if recipient.recipient else "Unknown",
                        "contact_role": "distributor",
                        "initial_message": inquiry.message,
                        "initial_image": inquiry.image_url,
                        "unread_count": unread_count,
                        "last_message": last_message.message if last_message else inquiry.message,
                        "last_message_time": (last_message.created_at.isoformat() if last_message 
                                              else inquiry.created_at.isoformat()),
                        "status": recipient.status,
                        "created_at": inquiry.created_at.isoformat()
                    })

        elif role == "distributor":
            # Get all inquiry recipients for this distributor
            recipients = InquiryRecipient.query.filter_by(recipient_id=user_id)\
                .order_by(InquiryRecipient.created_at.desc()).all()
            
            for recipient in recipients:
                inquiry = recipient.inquiry
                sender = inquiry.sender
                shop = sender.shops.first() if sender else None
                
                # Count unread messages (messages from shop owner that distributor hasn't read)
                unread_count = InquiryMessage.query.filter(
                    InquiryMessage.inquiry_recipient_id == recipient.id,
                    InquiryMessage.sender_id != user_id,
                    InquiryMessage.is_read == False
                ).count()
                
                # Also count initial inquiry as unread if not yet viewed
                if recipient.status == "pending":
                    unread_count += 1
                
                # Get last message
                last_message = InquiryMessage.query.filter_by(
                    inquiry_recipient_id=recipient.id
                ).order_by(InquiryMessage.created_at.desc()).first()
                
                conversations.append({
                    "id": recipient.id,
                    "inquiry_id": inquiry.id,
                    "contact_id": sender.id if sender else None,
                    "contact_name": sender.full_name if sender else "Unknown",
                    "shop_name": shop.name if shop else "Unknown Shop",
                    "contact_role": "shop_owner",
                    "initial_message": inquiry.message,
                    "initial_image": inquiry.image_url,
                    "unread_count": unread_count,
                    "last_message": last_message.message if last_message else inquiry.message,
                    "last_message_time": (last_message.created_at.isoformat() if last_message 
                                          else inquiry.created_at.isoformat()),
                    "status": recipient.status,
                    "created_at": inquiry.created_at.isoformat()
                })

        # Sort by last message time
        conversations.sort(key=lambda x: x["last_message_time"], reverse=True)

        return jsonify({
            "status": "success",
            "count": len(conversations),
            "conversations": conversations
        }), 200

    except Exception as e:
        print("Get conversations error:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to fetch conversations",
            "error": str(e)
        }), 500


@inquiry_bp.route("/conversation/<int:conversation_id>/messages", methods=["GET"])
@token_required
def get_conversation_messages(current_user, conversation_id):
    """
    Get all messages for a specific conversation thread.
    Includes the initial inquiry message as the first message.
    """
    try:
        user_id = current_user.get("id")
        role = current_user.get("role", "").lower()
        
        # Get the inquiry recipient (conversation thread)
        recipient = InquiryRecipient.query.get(conversation_id)
        if not recipient:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404
        
        inquiry = recipient.inquiry
        
        # Verify user has access to this conversation
        is_shop_owner = inquiry.sender_id == user_id
        is_distributor = recipient.recipient_id == user_id
        
        if not (is_shop_owner or is_distributor):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Mark conversation as read for distributor (first view)
        if is_distributor and recipient.status == "pending":
            recipient.status = "read"
            recipient.read_at = datetime.utcnow()
            db.session.commit()
        
        # Mark all messages from the other party as read
        InquiryMessage.query.filter(
            InquiryMessage.inquiry_recipient_id == conversation_id,
            InquiryMessage.sender_id != user_id,
            InquiryMessage.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        db.session.commit()
        
        # Build messages list starting with initial inquiry
        messages = [{
            "id": f"inquiry_{inquiry.id}",
            "sender_id": inquiry.sender_id,
            "sender_name": inquiry.sender.full_name if inquiry.sender else "Unknown",
            "sender_role": inquiry.sender.role if inquiry.sender else "unknown",
            "message": inquiry.message,
            "image_url": inquiry.image_url,
            "is_read": True,  # Initial message is always considered read
            "read_at": recipient.read_at.isoformat() if recipient.read_at else None,
            "created_at": inquiry.created_at.isoformat(),
            "is_initial": True
        }]
        
        # Get all chat messages
        chat_messages = InquiryMessage.query.filter_by(
            inquiry_recipient_id=conversation_id
        ).order_by(InquiryMessage.created_at.asc()).all()
        
        for msg in chat_messages:
            messages.append(msg.to_chat_dict())
        
        # Get contact info
        if is_shop_owner:
            contact = recipient.recipient
            contact_info = {
                "id": contact.id,
                "name": contact.full_name,
                "email": contact.email,
                "role": "distributor"
            }
        else:
            contact = inquiry.sender
            shop = contact.shops.first() if contact else None
            contact_info = {
                "id": contact.id if contact else None,
                "name": contact.full_name if contact else "Unknown",
                "email": contact.email if contact else None,
                "role": "shop_owner",
                "shop_name": shop.name if shop else "Unknown Shop"
            }
        
        return jsonify({
            "status": "success",
            "conversation_id": conversation_id,
            "inquiry_id": inquiry.id,
            "contact": contact_info,
            "messages": messages,
            "conversation_status": recipient.status
        }), 200

    except Exception as e:
        print("Get conversation messages error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to fetch messages",
            "error": str(e)
        }), 500


@inquiry_bp.route("/conversation/<int:conversation_id>/send", methods=["POST"])
@token_required
def send_message(current_user, conversation_id):
    """
    Send a new message in a conversation thread.
    Supports text message and optional image attachment.
    """
    try:
        user_id = current_user.get("id")
        
        # Get the inquiry recipient (conversation thread)
        recipient = InquiryRecipient.query.get(conversation_id)
        if not recipient:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404
        
        inquiry = recipient.inquiry
        
        # Verify user has access to this conversation
        is_shop_owner = inquiry.sender_id == user_id
        is_distributor = recipient.recipient_id == user_id
        
        if not (is_shop_owner or is_distributor):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Get message data
        data = request.form or request.get_json(silent=True) or {}
        message_text = data.get("message", "").strip()
        
        if not message_text:
            return jsonify({"status": "error", "message": "Message cannot be empty"}), 400
        
        # Handle image upload
        file_path = None
        file = request.files.get("image")
        if file:
            is_valid, file_message = validate_file_upload(file, ['.png', '.jpg', '.jpeg', '.gif'], max_size_mb=10)
            if not is_valid:
                return jsonify({"status": "error", "message": file_message}), 400
            file_path = save_inquiry_file(file)
        
        # Create the message
        new_message = InquiryMessage(
            inquiry_recipient_id=conversation_id,
            sender_id=user_id,
            message=message_text,
            image_url=file_path.replace("\\", "/") if file_path else None
        )
        db.session.add(new_message)
        
        # Update recipient status to 'replied' if this is a distributor responding
        if is_distributor and recipient.status != "replied":
            recipient.status = "replied"
        
        # Create notification for the other party
        if is_shop_owner:
            # Notify distributor
            notification_user_id = recipient.recipient_id
            notification_message = f"New message from {current_user.get('username')}"
        else:
            # Notify shop owner
            notification_user_id = inquiry.sender_id
            notification_message = f"Reply from distributor {current_user.get('username')}"
        
        notification = Notification(
            user_id=notification_user_id,
            message=notification_message,
            link=f"/inquiries/chat/{conversation_id}",
            is_read=False
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Message sent successfully",
            "data": new_message.to_chat_dict()
        }), 201

    except Exception as e:
        print("Send message error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to send message",
            "error": str(e)
        }), 500


@inquiry_bp.route("/conversation/<int:conversation_id>/mark-read", methods=["PUT"])
@token_required
def mark_conversation_read(current_user, conversation_id):
    """Mark all messages in a conversation as read for the current user."""
    try:
        user_id = current_user.get("id")
        
        # Get the inquiry recipient (conversation thread)
        recipient = InquiryRecipient.query.get(conversation_id)
        if not recipient:
            return jsonify({"status": "error", "message": "Conversation not found"}), 404
        
        inquiry = recipient.inquiry
        
        # Verify user has access
        is_shop_owner = inquiry.sender_id == user_id
        is_distributor = recipient.recipient_id == user_id
        
        if not (is_shop_owner or is_distributor):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Mark all messages from the other party as read
        updated = InquiryMessage.query.filter(
            InquiryMessage.inquiry_recipient_id == conversation_id,
            InquiryMessage.sender_id != user_id,
            InquiryMessage.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        # Update recipient status if distributor first viewing
        if is_distributor and recipient.status == "pending":
            recipient.status = "read"
            recipient.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Marked {updated} messages as read"
        }), 200

    except Exception as e:
        print("Mark read error:", e)
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to mark messages as read",
            "error": str(e)
        }), 500


@inquiry_bp.route("/unread-count", methods=["GET"])
@token_required
def get_unread_count(current_user):
    """Get total unread message count for the current user."""
    try:
        user_id = current_user.get("id")
        role = current_user.get("role", "").lower()
        total_unread = 0

        if role in ["shop_owner", "shop_manager"]:
            # Count unread messages in conversations where user is the shop owner
            inquiries = Inquiry.query.filter_by(sender_id=user_id).all()
            for inquiry in inquiries:
                for recipient in inquiry.recipients:
                    total_unread += InquiryMessage.query.filter(
                        InquiryMessage.inquiry_recipient_id == recipient.id,
                        InquiryMessage.sender_id != user_id,
                        InquiryMessage.is_read == False
                    ).count()

        elif role == "distributor":
            # Count unread messages and pending inquiries
            recipients = InquiryRecipient.query.filter_by(recipient_id=user_id).all()
            for recipient in recipients:
                # Count unread chat messages
                total_unread += InquiryMessage.query.filter(
                    InquiryMessage.inquiry_recipient_id == recipient.id,
                    InquiryMessage.sender_id != user_id,
                    InquiryMessage.is_read == False
                ).count()
                # Count pending initial inquiries
                if recipient.status == "pending":
                    total_unread += 1

        return jsonify({
            "status": "success",
            "unread_count": total_unread
        }), 200

    except Exception as e:
        print("Unread count error:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to get unread count",
            "error": str(e)
        }), 500
