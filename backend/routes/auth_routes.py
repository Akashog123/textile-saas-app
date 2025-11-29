# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from models.model import db, User, Shop
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt, os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import or_


# Environment Setup
load_dotenv()
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# JWT Utility Functions (kept for token verify)
def generate_jwt(user):
    secret_key = os.getenv("SECRET_KEY", "default-secret-key")
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token):
    try:
        secret_key = os.getenv("SECRET_KEY", "default-secret-key")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Token missing or invalid."}), 401

        token = auth_header.split(" ")[1]
        decoded = decode_jwt(token)
        if not decoded:
            return jsonify({"message": "Invalid or expired token."}), 401

        return f(decoded, *args, **kwargs)
    return decorated


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
def session_check(decoded):
    try:
        user = User.query.get(decoded.get("user_id"))
        if not user:
            return jsonify({"status": "error", "message": "User not found."}), 404

        return jsonify({
            "status": "success",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "approved": user.approved
            }
        }), 200

    except Exception as e:
        print(f"[Error - Session Check] {e}")
        return jsonify({"status": "error", "message": "Session validation failed.", "error": str(e)}), 500


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
