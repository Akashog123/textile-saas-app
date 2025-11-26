# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from models.model import db, User, Shop
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from utils.auth_utils import generate_jwt, decode_jwt, token_required
from utils.validation import validate_password
from datetime import datetime


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# JWT utilities are now imported from utils.auth_utils


# Register (Sign Up)
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register new users for all roles, auto-creates Shop for shop_owners."""
    try:
        data = request.get_json() or {}

        required_fields = ["full_name", "username", "password", "role"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

        for k, v in data.items():
            if isinstance(v, str) and v.strip() == "":
                data[k] = None

        if not data.get("email"):
            data["email"] = f"{data['username']}@noemail.com"

        # Validate password strength
        is_valid, password_message = validate_password(data["password"])
        if not is_valid:
            return jsonify({"status": "error", "message": password_message}), 400

        # Prevent duplicates
        duplicate = User.query.filter(
            or_(User.username == data["username"], User.email == data["email"])
        ).first()
        if duplicate:
            return jsonify({"status": "error", "message": "Username or email already exists."}), 400

        hashed_pw = generate_password_hash(data["password"])

        new_user = User(
            full_name=data["full_name"],
            username=data["username"],
            email=data["email"],
            password=hashed_pw,
            role=data.get("role", "customer"),
            contact=data.get("contact"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            pincode=data.get("pincode"),
            approved=True if data.get("role") != "professional" else False,
        )

        db.session.add(new_user)
        db.session.commit()

        # Auto-create Shop for Shop Owners
        if new_user.role.lower() == "shop_owner":
            shop_name = f"{new_user.full_name or new_user.username}'s Shop"
            location = new_user.city or "Unspecified"

            new_shop = Shop(
                name=shop_name,
                description="Newly registered shop",
                location=location,
                owner_id=new_user.id
            )
            db.session.add(new_shop)
            db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Account created successfully!",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "full_name": new_user.full_name,
                "approved": new_user.approved
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Register] {e}")
        return jsonify({
            "status": "error",
            "message": "Registration failed.",
            "error": str(e)
        }), 500


# Login (Sign In)
@auth_bp.route("/login", methods=["POST"])
def login():
    """Simple login (supports username or email)."""
    try:
        data = request.get_json() or {}
        identifier = data.get("username")
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"status": "error", "message": "Username and password required."}), 400

        user = User.query.filter(
            or_(
                db.func.lower(User.username) == identifier.lower(),
                db.func.lower(User.email) == identifier.lower()
            )
        ).first()

        if not user or not check_password_hash(user.password, password):
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401

        if user.role.lower() == "professional" and not user.approved:
            return jsonify({"status": "error", "message": "Account awaiting admin approval."}), 403
        
        # Update last login timestamp (session tracking)
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        # Include shop_id if user is a shop_owner
        shop_id = None
        if user.role.lower() == "shop_owner":
            shop = Shop.query.filter_by(owner_id=user.id).first()
            if shop:
                shop_id = shop.id

        token = generate_jwt(user)

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "shop_id": shop_id
            }
        }), 200

    except Exception as e:
        print(f"[Error - Login] {e}")
        return jsonify({
            "status": "error",
            "message": "Login failed.",
            "error": str(e)
        }), 500


# Session Validation (JWT based)
@auth_bp.route("/session", methods=["GET"])
@token_required
def session_check(current_user):
    try:
        # current_user is already injected by @token_required decorator
        user_id = current_user.get("id")

        return jsonify({
            "status": "success",
            "user": current_user
        }), 200

    except Exception as e:
        print(f"[Error - Session Check] {e}")
        return jsonify({"status": "error", "message": "Session validation failed."}), 500


# Token Verification
@auth_bp.route("/verify_token", methods=["POST", "OPTIONS"])
def verify_token():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    try:
        data = request.get_json() or {}
        token = data.get("token")
        if not token:
            return jsonify({"status": "error", "message": "Token missing."}), 400

        decoded = decode_jwt(token)
        if not decoded:
            return jsonify({"status": "error", "message": "Invalid or expired token."}), 401

        user = User.query.get(decoded.get("user_id"))
        if not user:
            return jsonify({"status": "error", "message": "User not found."}), 404

        return jsonify({
            "status": "success",
            "message": "Token valid.",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "full_name": user.full_name,
                "approved": user.approved
            }
        }), 200

    except Exception as e:
        print(f"[Error - Verify Token] {e}")
        return jsonify({"status": "error", "message": "Token verification failed.", "error": str(e)}), 500


# Logout
@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"status": "success", "message": "Logout successful. Please clear token on client."}), 200
