# routes/profile_routes.py

from flask import Blueprint, request
from models.model import db, User, Shop
from utils.auth_utils import token_required
from utils.response_helpers import (
    success_response, error_response, not_found_response, handle_exceptions
)

profile_bp = Blueprint("profile", __name__)


def _serialize_shop_for_profile(shop):
    """Serialize a shop for profile response."""
    return {
        "id": shop.id,
        "name": shop.name or "",
        "shop_name": shop.name or "",
        "description": shop.description or "",
        "address": shop.address or "",
        "city": shop.city or "",
        "state": shop.state or "",
        "location": shop.location or "",
        "contact": shop.contact or "",
        "gstin": shop.gstin or "",
        "lat": shop.lat,
        "lon": shop.lon,
        "latitude": shop.lat,
        "longitude": shop.lon,
        "rating": round(shop.rating or 4.0, 1),
        "is_popular": shop.is_popular or False,
        "image_url": shop.image_url or "",
        "product_count": shop.products.count(),
        "review_count": shop.reviews.count(),
        "created_at": shop.created_at.isoformat() if shop.created_at else None,
    }


# Fetch Current User Profile
@profile_bp.route("/", methods=["GET"])
@token_required
@handle_exceptions("Fetch Profile")
def get_profile(current_user):
    """Fetch the logged-in user's profile details including all shops."""
    user = User.query.get(current_user.get("id"))
    if not user:
        return not_found_response("User")

    # Build profile data with fallbacks for empty values
    profile_data = {
        "id": user.id,
        "full_name": user.full_name or "",
        "username": user.username or "",
        "email": user.email or "",
        "contact": user.contact or "",
        "address": user.address or "",
        "city": user.city or "",
        "state": user.state or "",
        "pincode": user.pincode or "",
        "role": user.role or "customer",
        "approved": user.approved,
        "avatar_url": user.avatar_url or "",
        "bio": user.bio or "",
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "primary_shop_id": user.primary_shop_id,
    }
    
    # Add ALL shops for shop owners/managers
    shops_list = []
    primary_shop_data = None
    
    if user.role in ["shop_owner", "admin", "shop_manager"]:
        # Get all shops owned by user
        all_shops = user.shops.order_by(Shop.created_at.desc()).all()
        shops_list = [_serialize_shop_for_profile(s) for s in all_shops]
        
        # Mark primary shop and get primary shop data
        primary_shop = user.get_primary_shop()
        if primary_shop:
            primary_shop_data = _serialize_shop_for_profile(primary_shop)
            # Mark which shop is primary in the list
            for shop in shops_list:
                shop["is_primary"] = shop["id"] == primary_shop.id
    
    # For backward compatibility, also include single shop fields
    profile_data["shop"] = primary_shop_data
    profile_data["shop_name"] = primary_shop_data["name"] if primary_shop_data else None
    profile_data["shop_id"] = primary_shop_data["id"] if primary_shop_data else None
    
    # New: include all shops
    profile_data["shops"] = shops_list
    profile_data["shop_count"] = len(shops_list)

    # Return profile directly to match frontend expectations
    return success_response(
        message="Profile fetched successfully.",
        profile=profile_data
    )


# Update User Profile
@profile_bp.route("/update", methods=["PUT"])
@token_required
@handle_exceptions("Update Profile")
def update_profile(current_user):
    """
    Update current user's profile fields dynamically.
    Only allows editing of basic info (not role or approval).
    """
    data = request.get_json(force=True, silent=True) or {}
    user = User.query.get(current_user.get("id"))

    if not user:
        return not_found_response("User")

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
        return error_response("No valid fields to update.", 400)

    db.session.commit()

    return success_response(
        message="Profile updated successfully!",
        updated_fields=updated_fields
    )


# Set Primary Shop
@profile_bp.route("/primary-shop", methods=["PUT"])
@token_required
@handle_exceptions("Set Primary Shop")
def set_primary_shop(current_user):
    """
    Set the primary/active shop for the current user.
    Expects JSON: { "shop_id": <int> }
    """
    data = request.get_json(force=True, silent=True) or {}
    user = User.query.get(current_user.get("id"))

    if not user:
        return not_found_response("User")

    if user.role not in ["shop_owner", "admin", "shop_manager"]:
        return error_response("Only shop owners can set a primary shop.", 403)

    shop_id = data.get("shop_id")
    if not shop_id:
        return error_response("shop_id is required.", 400)

    try:
        shop_id = int(shop_id)
    except (ValueError, TypeError):
        return error_response("Invalid shop_id.", 400)

    # Verify shop belongs to user
    shop = Shop.query.filter_by(id=shop_id, owner_id=user.id).first()
    if not shop:
        return error_response("Shop not found or not owned by you.", 404)

    user.primary_shop_id = shop_id
    db.session.commit()

    return success_response(
        message=f"Primary shop set to '{shop.name}'.",
        primary_shop_id=shop_id,
        shop_name=shop.name
    )