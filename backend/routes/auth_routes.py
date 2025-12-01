# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from models.model import db, User, Shop
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from utils.auth_utils import generate_jwt, decode_jwt, token_required
from utils.validation import validate_password
from utils.response_helpers import (
    success_response, error_response, created_response, 
    not_found_response, handle_exceptions
)
from datetime import datetime


auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# Register (Sign Up)
@auth_bp.route("/register", methods=["POST"])
@handle_exceptions("Register")
def register():
    """Register new users for all roles, auto-creates Shop for shop_owners."""
    data = request.get_json() or {}

    required_fields = ["full_name", "username", "password", "role"]
    for field in required_fields:
        if not data.get(field):
            return error_response(f"Missing required field: {field}", 400)

    for k, v in data.items():
        if isinstance(v, str) and v.strip() == "":
            data[k] = None

    if not data.get("email"):
        data["email"] = f"{data['username']}@noemail.com"

    # Validate password strength
    is_valid, password_message = validate_password(data["password"])
    if not is_valid:
        return error_response(password_message, 400)

    # Prevent duplicates
    duplicate = User.query.filter(
        or_(User.username == data["username"], User.email == data["email"])
    ).first()
    if duplicate:
        return error_response("Username or email already exists.", 400)

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

    return created_response(
        data={"user": new_user.to_auth_dict()},
        message="Account created successfully!"
    )


# Login (Sign In)
@auth_bp.route("/login", methods=["POST"])
@handle_exceptions("Login")
def login():
    """Simple login (supports username or email)."""
    data = request.get_json() or {}
    identifier = data.get("username")
    password = data.get("password")

    if not identifier or not password:
        return error_response("Username and password required.", 400)

    user = User.query.filter(
        or_(
            db.func.lower(User.username) == identifier.lower(),
            db.func.lower(User.email) == identifier.lower()
        )
    ).first()

    if not user or not check_password_hash(user.password, password):
        return error_response("Invalid credentials.", 401)

    if user.role.lower() == "professional" and not user.approved:
        return error_response("Account awaiting admin approval.", 403)
    
    # Update last login timestamp (session tracking)
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    token = generate_jwt(user)

    return success_response(
        message="Login successful",
        token=token,
        user=user.to_auth_dict(include_shop=True)
    )


# Session Validation (JWT based)
@auth_bp.route("/session", methods=["GET"])
@token_required
@handle_exceptions("Session Check")
def session_check(current_user):
    # current_user is already injected by @token_required decorator
    user_id = current_user.get("id")
    
    # Check if user still exists and is approved
    user = User.query.get(user_id)
    if not user:
        return error_response("User no longer exists.", 401)
    
    # Check approval status for professional users
    if user.role == "professional" and not user.approved:
        return error_response("Account pending approval.", 403)

    return success_response(user=current_user)


# Token Verification
@auth_bp.route("/verify_token", methods=["POST", "OPTIONS"])
@handle_exceptions("Verify Token")
def verify_token():
    if request.method == "OPTIONS":
        return success_response(message="CORS preflight successful")

    data = request.get_json() or {}
    token = data.get("token")
    if not token:
        return error_response("Token missing.", 400)

    decoded = decode_jwt(token)
    if not decoded:
        return error_response("Invalid or expired token.", 401)

    user = User.query.get(decoded.get("user_id"))
    if not user:
        return not_found_response("User")

    return success_response(
        message="Token valid.",
        user=user.to_auth_dict()
    )


# Logout
@auth_bp.route("/logout", methods=["POST"])
def logout():
    return success_response(message="Logout successful. Please clear token on client.")
