# routes/review_routes.py
"""
Customer Reviews API for Shops and Products
Production-ready implementation with authentication and auto user name fetching.
"""
from flask import Blueprint, request, jsonify, current_app
from models.model import db, Review, User, Shop, Product
from utils.auth_utils import token_required
from datetime import datetime
from sqlalchemy import func

reviews_bp = Blueprint("reviews", __name__)


# ============================================================================
# GET REVIEWS
# ============================================================================

@reviews_bp.route("/customer/shops/<int:shop_id>/reviews", methods=["GET"])
def get_shop_reviews(shop_id):
    """
    Get all reviews for a specific shop.
    Public endpoint - no authentication required for viewing.
    """
    try:
        # Verify shop exists
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        # Optimized query: fetch reviews with explicit ordering
        reviews = Review.query.filter(Review.shop_id == shop_id).order_by(Review.created_at.desc()).all()

        # Build frontend-friendly reviews list
        reviews_list = []
        for r in reviews:
            # Fetch user info if user_id exists
            user = User.query.get(r.user_id) if r.user_id else None
            reviews_list.append({
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.user_name or (user.full_name if user else "Anonymous"),
                "rating": r.rating,
                "title": r.title or "",
                "body": r.body or "",
                "is_verified": bool(getattr(r, "is_verified_purchase", False)),
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None
            })

        # Aggregates in single query
        agg = db.session.query(
            func.avg(Review.rating).label("avg"), 
            func.count(Review.id).label("count")
        ).filter(Review.shop_id == shop_id).one()
        
        avg_rating = float(agg.avg) if agg.avg is not None else 0.0
        review_count = int(agg.count or 0)

        return jsonify({
            "status": "success",
            "reviews": reviews_list, 
            "avgRating": round(avg_rating, 2), 
            "reviewCount": review_count,
            "shop_name": shop.name
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Error fetching reviews")
        return jsonify({"status": "error", "message": "Failed to load reviews"}), 500


@reviews_bp.route("/customer/reviews/my-reviews", methods=["GET"])
@token_required
def get_my_reviews(current_user):
    """
    Get all reviews submitted by the authenticated user.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        if not user_id:
            return jsonify({"status": "error", "message": "User not found"}), 401
        
        reviews = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc()).all()
        
        reviews_list = []
        for r in reviews:
            shop = Shop.query.get(r.shop_id) if r.shop_id else None
            reviews_list.append({
                "id": r.id,
                "rating": r.rating,
                "title": r.title,
                "body": r.body or "",
                "shop_id": r.shop_id,
                "shop_name": shop.name if shop else None,
                "is_verified": bool(getattr(r, "is_verified_purchase", False)),
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        
        return jsonify({
            "status": "success",
            "reviews": reviews_list,
            "count": len(reviews_list)
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Error fetching user reviews")
        return jsonify({"status": "error", "message": "Failed to load reviews"}), 500


# ============================================================================
# CREATE REVIEW
# ============================================================================

@reviews_bp.route("/customer/shops/<int:shop_id>/reviews", methods=["POST"])
@token_required
def post_shop_review(current_user, shop_id):
    """
    Submit a review for a shop.
    Requires authentication - user name is auto-fetched from token.
    """
    try:
        data = request.get_json(force=True)
        rating = data.get("rating")
        title = data.get("title", "")
        comment = data.get("comment") or data.get("body") or ""

        # Validate rating
        if rating is None or not (1 <= int(rating) <= 5):
            return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400
        
        # Validate comment
        if len(comment.strip()) < 1:
            return jsonify({"status": "error", "message": "Review comment is required"}), 400

        # Verify shop exists
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404

        # Get user info from authenticated token (auto-fetch name)
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        # Fetch user from database to get full name
        user = User.query.get(user_id) if user_id else None
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 401
        
        # Use full_name from database, not manual input
        user_name = user.full_name or user.username

        # Check if user already reviewed this shop (one review per user per shop)
        existing_review = Review.query.filter_by(user_id=user_id, shop_id=shop_id).first()
        if existing_review:
            return jsonify({
                "status": "error", 
                "message": "You have already reviewed this shop. Edit your existing review instead."
            }), 409

        # Create review with auto-fetched user info
        review = Review(
            user_id=user_id,
            user_name=user_name,
            product_id=None,
            shop_id=shop_id,
            rating=int(rating),
            title=title.strip() if title else None,
            body=comment.strip(),
            is_verified_purchase=True  # Customer is verified via token
        )

        db.session.add(review)
        
        # Update shop's average rating
        _update_shop_rating(shop_id)
        
        db.session.commit()

        # Prepare response
        saved = {
            "id": review.id,
            "user_id": review.user_id,
            "user_name": review.user_name,
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "is_verified": True,
            "created_at": review.created_at.isoformat() if review.created_at else None
        }

        return jsonify({
            "status": "success", 
            "message": "Review submitted successfully",
            "review": saved
        }), 201

    except Exception as e:
        current_app.logger.exception("Failed to submit review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to submit review"}), 500


# ============================================================================
# UPDATE REVIEW
# ============================================================================

@reviews_bp.route("/customer/reviews/<int:review_id>", methods=["PUT"])
@token_required
def update_review(current_user, review_id):
    """
    Update an existing review (only by the review author).
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"status": "error", "message": "Review not found"}), 404
        
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only edit your own reviews"}), 403
        
        data = request.get_json(force=True)
        
        # Update fields if provided
        if "rating" in data:
            rating = data["rating"]
            if not (1 <= int(rating) <= 5):
                return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400
            review.rating = int(rating)
        
        if "title" in data:
            review.title = data["title"].strip() if data["title"] else None
        
        if "body" in data or "comment" in data:
            comment = data.get("body") or data.get("comment") or ""
            if len(comment.strip()) < 1:
                return jsonify({"status": "error", "message": "Review comment is required"}), 400
            review.body = comment.strip()
        
        review.updated_at = datetime.utcnow()
        
        # Update shop rating
        if review.shop_id:
            _update_shop_rating(review.shop_id)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Review updated successfully",
            "review": {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "body": review.body,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to update review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to update review"}), 500


@reviews_bp.route("/customer/shops/<int:shop_id>/reviews/<int:review_id>", methods=["PUT"])
@token_required
def update_shop_review(current_user, shop_id, review_id):
    """
    Update a review for a specific shop (shop_id in URL for API compatibility).
    Only the review author can update their review.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        # Verify the review exists AND belongs to this shop
        review = Review.query.filter_by(id=review_id, shop_id=shop_id).first()
        if not review:
            return jsonify({"status": "error", "message": "Review not found for this shop"}), 404
        
        # Check ownership
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only edit your own reviews"}), 403
        
        data = request.get_json(force=True)
        
        # Update fields if provided
        if "rating" in data:
            rating = data["rating"]
            if not (1 <= int(rating) <= 5):
                return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400
            review.rating = int(rating)
        
        if "title" in data:
            review.title = data["title"].strip() if data["title"] else None
        
        if "body" in data or "comment" in data:
            comment = data.get("body") or data.get("comment") or ""
            if len(comment.strip()) < 1:
                return jsonify({"status": "error", "message": "Review comment is required"}), 400
            review.body = comment.strip()
        
        review.updated_at = datetime.utcnow()
        
        # Update shop rating
        _update_shop_rating(shop_id)
        
        db.session.commit()
        
        # Get user name for response
        user = User.query.get(user_id)
        user_name = review.user_name or (user.full_name if user else "Anonymous")
        
        return jsonify({
            "status": "success",
            "message": "Review updated successfully",
            "review": {
                "id": review.id,
                "user_name": user_name,
                "rating": review.rating,
                "title": review.title,
                "body": review.body,
                "is_verified": bool(getattr(review, "is_verified_purchase", False)),
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to update review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to update review"}), 500


# ============================================================================
# DELETE REVIEW
# ============================================================================

@reviews_bp.route("/customer/reviews/<int:review_id>", methods=["DELETE"])
@token_required
def delete_review(current_user, review_id):
    """
    Delete a review (only by the review author).
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"status": "error", "message": "Review not found"}), 404
        
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only delete your own reviews"}), 403
        
        shop_id = review.shop_id
        db.session.delete(review)
        
        # Update shop rating after deletion
        if shop_id:
            _update_shop_rating(shop_id)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Review deleted successfully"
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to delete review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete review"}), 500


@reviews_bp.route("/customer/shops/<int:shop_id>/reviews/<int:review_id>", methods=["DELETE"])
@token_required
def delete_shop_review(current_user, shop_id, review_id):
    """
    Delete a review for a specific shop (shop_id in URL for API compatibility).
    Only the review author can delete their review.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        # Verify the review exists AND belongs to this shop
        review = Review.query.filter_by(id=review_id, shop_id=shop_id).first()
        if not review:
            return jsonify({"status": "error", "message": "Review not found for this shop"}), 404
        
        # Check ownership
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only delete your own reviews"}), 403
        
        db.session.delete(review)
        
        # Update shop rating after deletion
        _update_shop_rating(shop_id)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Review deleted successfully"
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to delete review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete review"}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _update_shop_rating(shop_id: int):
    """
    Helper to recalculate and update shop's average rating.
    """
    try:
        agg = db.session.query(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("count")
        ).filter(Review.shop_id == shop_id).one()
        
        shop = Shop.query.get(shop_id)
        if shop:
            shop.rating = float(agg.avg) if agg.avg else 0.0  # Default to 0.0 if no reviews
            # Optionally store review count if shop model has it
            if hasattr(shop, 'review_count'):
                shop.review_count = int(agg.count or 0)
    except Exception as e:
        current_app.logger.warning(f"Failed to update shop rating: {e}")


# ============================================================================
# PRODUCT REVIEW ENDPOINTS
# ============================================================================

@reviews_bp.route("/customer/products/<int:product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id):
    """
    Get all reviews for a specific product.
    Public endpoint.
    """
    try:
        # Verify product exists
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        # Fetch reviews
        reviews = Review.query.filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()

        reviews_list = []
        for r in reviews:
            user = db.session.get(User, r.user_id) if r.user_id else None
            reviews_list.append({
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.user_name or (user.full_name if user else "Anonymous"),
                "rating": r.rating,
                "title": r.title or "",
                "body": r.body or "",
                "is_verified": bool(getattr(r, "is_verified_purchase", False)),
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None
            })

        # Aggregates
        agg = db.session.query(
            func.avg(Review.rating).label("avg"), 
            func.count(Review.id).label("count")
        ).filter(Review.product_id == product_id).one()
        
        avg_rating = float(agg.avg) if agg.avg is not None else 0.0
        review_count = int(agg.count or 0)

        return jsonify({
            "status": "success",
            "reviews": reviews_list, 
            "avgRating": round(avg_rating, 2), 
            "reviewCount": review_count,
            "product_name": product.name
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Error fetching product reviews")
        return jsonify({"status": "error", "message": "Failed to load reviews"}), 500


@reviews_bp.route("/customer/products/<int:product_id>/reviews", methods=["POST"])
@token_required
def post_product_review(current_user, product_id):
    """
    Submit a review for a product.
    Enforces one review per user per product.
    """
    try:
        data = request.get_json(force=True)
        rating = data.get("rating")
        title = data.get("title", "")
        comment = data.get("comment") or data.get("body") or ""

        # Validate rating
        if rating is None or not (1 <= int(rating) <= 5):
            return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400
        
        if len(comment.strip()) < 1:
            return jsonify({"status": "error", "message": "Review comment is required"}), 400

        # Verify product exists
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404

        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        user = db.session.get(User, user_id) if user_id else None
        
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 401
        
        user_name = user.full_name or user.username

        # Check existing review
        existing_review = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing_review:
            return jsonify({
                "status": "error", 
                "message": "You have already reviewed this product. Edit your existing review instead."
            }), 409

        # Create review
        review = Review(
            user_id=user_id,
            user_name=user_name,
            product_id=product_id,
            shop_id=None,  # This is a product review
            rating=int(rating),
            title=title.strip() if title else None,
            body=comment.strip(),
            is_verified_purchase=True
        )

        db.session.add(review)
        
        # Update product rating
        _update_product_rating(product_id)
        
        db.session.commit()

        saved = {
            "id": review.id,
            "user_id": review.user_id,
            "user_name": review.user_name,
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "is_verified": True,
            "created_at": review.created_at.isoformat() if review.created_at else None
        }

        return jsonify({
            "status": "success", 
            "message": "Review submitted successfully",
            "review": saved
        }), 201

    except Exception as e:
        current_app.logger.exception("Failed to submit product review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to submit review"}), 500


@reviews_bp.route("/customer/products/<int:product_id>/reviews/<int:review_id>", methods=["PUT"])
@token_required
def update_product_review(current_user, product_id, review_id):
    """
    Update a product review.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        review = Review.query.filter_by(id=review_id, product_id=product_id).first()
        if not review:
            return jsonify({"status": "error", "message": "Review not found for this product"}), 404
        
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only edit your own reviews"}), 403
        
        data = request.get_json(force=True)
        
        if "rating" in data:
            rating = data["rating"]
            if not (1 <= int(rating) <= 5):
                return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400
            review.rating = int(rating)
        
        if "title" in data:
            review.title = data["title"].strip() if data["title"] else None
        
        if "body" in data or "comment" in data:
            comment = data.get("body") or data.get("comment") or ""
            if len(comment.strip()) < 1:
                return jsonify({"status": "error", "message": "Review comment is required"}), 400
            review.body = comment.strip()
        
        review.updated_at = datetime.utcnow()
        
        # Update product rating
        _update_product_rating(product_id)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Review updated successfully",
            "review": {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "body": review.body,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to update review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to update review"}), 500


@reviews_bp.route("/customer/products/<int:product_id>/reviews/<int:review_id>", methods=["DELETE"])
@token_required
def delete_product_review(current_user, product_id, review_id):
    """
    Delete a product review.
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None)
        
        review = Review.query.filter_by(id=review_id, product_id=product_id).first()
        if not review:
            return jsonify({"status": "error", "message": "Review not found for this product"}), 404
        
        if review.user_id != user_id:
            return jsonify({"status": "error", "message": "You can only delete your own reviews"}), 403
        
        db.session.delete(review)
        
        _update_product_rating(product_id)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Review deleted successfully"
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Failed to delete review")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete review"}), 500


def _update_product_rating(product_id: int):
    """
    Helper to recalculate and update product's average rating.
    """
    try:
        agg = db.session.query(
            func.avg(Review.rating).label("avg")
        ).filter(Review.product_id == product_id).one()
        
        product = db.session.get(Product, product_id)
        if product:
            product.rating = float(agg.avg) if agg.avg else 0.0
    except Exception as e:
        current_app.logger.warning(f"Failed to update product rating: {e}")
