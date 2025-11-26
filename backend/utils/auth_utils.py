# backend/utils/auth_utils.py
"""
Authentication and Authorization Utilities
Provides JWT handling, authentication decorators, and RBAC (Role-Based Access Control)
"""

import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from models.model import db, User, Shop, Product
from dotenv import load_dotenv

load_dotenv()

# JWT Utilities
def generate_jwt(user, expiration_days=None):
    """
    Generate JWT token for authenticated user.
    
    Args:
        user: User model instance
        expiration_days: Token expiration in days (default from config: 7)
    
    Returns:
        str: Encoded JWT token
    """
    if expiration_days is None:
        expiration_days = int(os.getenv("JWT_EXPIRATION_DAYS", 7))
    
    secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "default-secret-key")
    
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(days=expiration_days),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")

def decode_jwt(token):
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY", "default-secret-key")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def extract_token_from_request():
    """
    Extract Bearer token from Authorization header.
    
    Returns:
        str: Token if found, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    return auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None


# Authentication Decorator
def token_required(f):
    """
    Decorator to require valid JWT token for endpoint access.
    Injects current_user dict into the wrapped function.
    
    Usage:
        @token_required
        def my_route(current_user):
            user_id = current_user['id']
            ...
    
    Returns:
        401: If token is missing or invalid
        Calls wrapped function with current_user if valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_request()
        
        if not token:
            return jsonify({"status": "error", "message": "Token missing or invalid."}), 401
        
        decoded = decode_jwt(token)
        if not decoded:
            return jsonify({"status": "error", "message": "Invalid or expired token."}), 401
        
        # Fetch fresh user data from database
        user = User.query.get(decoded.get("user_id"))
        if not user:
            return jsonify({"status": "error", "message": "User not found."}), 401
        
        # Inject current_user as dict
        current_user = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name,
            "email": user.email,
            "approved": user.approved
        }
        
        return f(current_user, *args, **kwargs)
    
    return decorated


# RBAC (Role-Based Access Control) Decorator
def roles_required(*allowed_roles):
    """
    Decorator to require specific user roles for endpoint access.
    MUST be used together with @token_required decorator.
    
    Args:
        *allowed_roles: Variable number of allowed role strings
    
    Usage:
        @token_required
        @roles_required('shop_owner', 'shop_manager')
        def my_route(current_user):
            ...
    
    Returns:
        403: If user doesn't have required role
        Calls wrapped function if user has one of the allowed roles
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            user_role = current_user.get("role", "").lower()
            
            # Normalize allowed roles to lowercase for comparison
            normalized_roles = [role.lower() for role in allowed_roles]
            
            if user_role not in normalized_roles:
                return jsonify({
                    "status": "error",
                    "message": f"Access denied. Required roles: {', '.join(allowed_roles)}"
                }), 403
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    
    return decorator


# Resource Ownership Validation Helpers
def check_shop_ownership(user_id, shop_id):
    """
    Check if user owns the specified shop.
    
    Args:
        user_id: User ID to check
        shop_id: Shop ID to validate
    
    Returns:
        bool: True if user owns shop, False otherwise
    """
    try:
        shop_id = int(shop_id)
        shop = Shop.query.filter_by(id=shop_id, owner_id=user_id).first()
        return shop is not None
    except (ValueError, TypeError):
        return False


def check_product_ownership(user_id, product_id):
    """
    Check if user owns the shop that contains the product.
    
    Args:
        user_id: User ID to check
        product_id: Product ID to validate
    
    Returns:
        bool: True if user owns the product (via shop ownership), False otherwise
    """
    try:
        product_id = int(product_id)
        product = Product.query.get(product_id)
        
        if not product:
            return False
        
        return check_shop_ownership(user_id, product.shop_id)
    except (ValueError, TypeError):
        return False


def get_user_shops(user_id):
    """
    Get list of shop IDs owned by user.
    
    Args:
        user_id: User ID
    
    Returns:
        list: List of shop IDs owned by user
    """
    shops = Shop.query.filter_by(owner_id=user_id).all()
    return [shop.id for shop in shops]


def resource_owner_required(resource_type, id_param='resource_id'):
    """
    Decorator to validate resource ownership.
    MUST be used together with @token_required decorator.
    
    Args:
        resource_type: Type of resource ('shop' or 'product')
        id_param: Name of parameter/query arg containing resource ID
    
    Usage:
        @token_required
        @resource_owner_required('shop', 'shop_id')
        def my_route(current_user, shop_id):
            ...
    
    Returns:
        403: If user doesn't own the resource
        400: If resource ID is invalid
        Calls wrapped function if ownership is validated
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            # Try to get resource ID from query params first, then from kwargs
            resource_id = request.args.get(id_param) or kwargs.get(id_param)
            
            if not resource_id:
                return jsonify({
                    "status": "error",
                    "message": f"{id_param} is required"
                }), 400
            
            user_id = current_user.get("id")
            
            # Validate ownership based on resource type
            if resource_type == 'shop':
                if not check_shop_ownership(user_id, resource_id):
                    return jsonify({
                        "status": "error",
                        "message": "You don't have permission to access this shop"
                    }), 403
            
            elif resource_type == 'product':
                if not check_product_ownership(user_id, resource_id):
                    return jsonify({
                        "status": "error",
                        "message": "You don't have permission to access this product"
                    }), 403
            
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid resource type"
                }), 500
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    
    return decorator



# Export all utilities

__all__ = [
    'generate_jwt',
    'decode_jwt',
    'extract_token_from_request',
    'token_required',
    'roles_required',
    'check_shop_ownership',
    'check_product_ownership',
    'get_user_shops',
    'resource_owner_required'
]
