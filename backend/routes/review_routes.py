# routes/review_routes.py
from flask import Blueprint, request, jsonify, current_app
from models.model import db, Review, User, Shop
from datetime import datetime
from sqlalchemy import func
from utils.auth_utils import token_required
import logging

logger = logging.getLogger(__name__)
reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.route("/customer/shops/<int:shop_id>/reviews", methods=["GET"])
def get_shop_reviews(shop_id):
    try:
        # Optimized query: fetch reviews with explicit ordering
        reviews = Review.query.filter(Review.shop_id == shop_id).order_by(Review.created_at.desc()).all()

        # Build frontend-friendly reviews list (no N+1 queries)
        # Since user_name is stored on Review model, use that directly
        reviews_list = [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.user_name or "Anonymous",
                "rating": r.rating,
                "title": r.title or "",
                "body": r.body or "",
                "is_verified": bool(getattr(r, "is_verified_purchase", False)),
                "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None
            }
            for r in reviews
        ]

        # Aggregates in single query
        agg = db.session.query(func.avg(Review.rating).label("avg"), func.count(Review.id).label("count")) \
                        .filter(Review.shop_id == shop_id).one()
        avg = float(agg.avg) if agg.avg is not None else 0.0
        count = int(agg.count or 0)

        return jsonify({"reviews": reviews_list, "avgRating": round(avg, 2), "reviewCount": count}), 200
    except Exception as e:
        current_app.logger.exception("Error fetching reviews")
        return jsonify({"message": "Failed to load reviews"}), 500


@reviews_bp.route("/customer/shops/<int:shop_id>/reviews", methods=["POST"])
@token_required
def post_shop_review(current_user, shop_id):
    try:
        data = request.get_json(force=True)
        rating = data.get("rating")
        title = data.get("title")
        comment = data.get("comment") or data.get("body") or ""
        is_verified = data.get("is_verified", True)

        if rating is None or not (1 <= int(rating) <= 5):
            return jsonify({"message": "rating must be integer between 1 and 5"}), 400
        if len(comment.strip()) < 1:
            return jsonify({"message": "comment/body is required"}), 400

        # Get user info from token (current_user is set by @token_required)
        user_id = current_user.get("id")
        user_name = current_user.get("full_name") or current_user.get("username")

        # Check if user already has a review for this shop (one review per user per shop)
        existing_review = Review.query.filter_by(user_id=user_id, shop_id=shop_id).first()
        if existing_review:
            return jsonify({"message": "You already have a review for this shop. Please edit or delete your existing review."}), 409

        # Create and save review
        review = Review(
            user_id=user_id,
            product_id=None,
            shop_id=shop_id,
            rating=int(rating),
            title=title,
            body=comment,
            user_name=user_name,
        )

        # If model contains `is_verified_purchase`, set it
        if hasattr(review, "is_verified_purchase"):
            review.is_verified_purchase = bool(is_verified)

        # Timestamp: ensure created_at field exists in model (TimestampMixin provides it)
        if not getattr(review, "created_at", None):
            review.created_at = datetime.utcnow()

        db.session.add(review)
        db.session.commit()

        # prepare response in frontend-friendly shape
        saved = {
            "id": review.id,
            "user_id": review.user_id,
            "user_name": review.user_name or "Anonymous",
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "is_verified": bool(getattr(review, "is_verified_purchase", False)),
            "created_at": review.created_at.isoformat() if review.created_at else None
        }

        return jsonify({"status": "success", "id": review.id, "review": saved}), 201

    except Exception as e:
        current_app.logger.exception("Failed to submit review")
        db.session.rollback()
        return jsonify({"message": "Failed to submit review"}), 500


@reviews_bp.route("/customer/shops/<int:shop_id>/reviews/<int:review_id>", methods=["PUT"])
@token_required
def update_shop_review(current_user, shop_id, review_id):
    try:
        review = Review.query.filter_by(id=review_id, shop_id=shop_id).first()
        if not review:
            return jsonify({"message": "Review not found"}), 404

        # Check if user owns this review
        if review.user_id != current_user.get("id"):
            return jsonify({"message": "You can only edit your own reviews"}), 403

        data = request.get_json(force=True)
        
        # Update fields
        if "rating" in data:
            rating = data.get("rating")
            if not (1 <= int(rating) <= 5):
                return jsonify({"message": "rating must be integer between 1 and 5"}), 400
            review.rating = int(rating)
        
        if "title" in data:
            review.title = data.get("title")
        
        if "body" in data or "comment" in data:
            comment = data.get("body") or data.get("comment") or ""
            if len(comment.strip()) < 1:
                return jsonify({"message": "comment/body is required"}), 400
            review.body = comment

        # Update the updated_at timestamp
        review.updated_at = datetime.utcnow()
        
        db.session.commit()

        # Prepare response
        saved = {
            "id": review.id,
            "user_id": review.user_id,
            "user_name": review.user_name or "Anonymous",
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "is_verified": bool(getattr(review, "is_verified_purchase", False)),
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "updated_at": review.updated_at.isoformat() if review.updated_at else None
        }

        return jsonify({"status": "success", "review": saved}), 200

    except Exception as e:
        current_app.logger.exception("Failed to update review")
        db.session.rollback()
        return jsonify({"message": "Failed to update review"}), 500


@reviews_bp.route("/customer/shops/<int:shop_id>/reviews/<int:review_id>", methods=["DELETE"])
@token_required
def delete_shop_review(current_user, shop_id, review_id):
    try:
        review = Review.query.filter_by(id=review_id, shop_id=shop_id).first()
        if not review:
            return jsonify({"message": "Review not found"}), 404

        # Check if user owns this review
        if review.user_id != current_user.get("id"):
            return jsonify({"message": "You can only delete your own reviews"}), 403

        db.session.delete(review)
        db.session.commit()

        return jsonify({"status": "success", "message": "Review deleted successfully"}), 200

    except Exception as e:
        current_app.logger.exception("Failed to delete review")
        db.session.rollback()
        return jsonify({"message": "Failed to delete review"}), 500

