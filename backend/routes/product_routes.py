# backend/routes/products.py

from flask import Blueprint, jsonify, request
from models.model import db, Product, Shop, SalesData
from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from utils.image_utils import resolve_product_image
from utils.performance_utils import cached_ai_caption, batch_ai_captions, performance_monitor
from services.ai_service import generate_ai_caption
from services.forecasting_service import top_trending_products
import pandas as pd

product_bp = Blueprint("product", __name__)

# GET: All Products (Dynamic + Filtered)
@product_bp.route("/", methods=["GET"])
@performance_monitor
def get_all_products():
    """
    Fetch all products dynamically with filtering and optional AI captions for Shop Managers only.
    Supports filters: category, price_min, price_max, search, generate_captions.
    """
    try:
        category = request.args.get("category")
        price_min = request.args.get("price_min", type=float)
        price_max = request.args.get("price_max", type=float)
        search = request.args.get("search")
        generate_captions = request.args.get("generate_captions", "false").lower() == "true"

        # Only allow AI caption generation for Shop Managers
        if generate_captions:
            from utils.auth_utils import get_current_user_from_token
            current_user = get_current_user_from_token()
            if not current_user or current_user.role not in ["shop_owner", "admin", "manager"]:
                generate_captions = False  # Deny AI generation for regular customers

        # Use joined query to avoid N+1 problem
        query = Product.query.join(Shop, Product.shop_id == Shop.id)

        # Apply filters dynamically
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        if price_min is not None:
            query = query.filter(Product.price >= price_min)
        if price_max is not None:
            query = query.filter(Product.price <= price_max)
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.category.ilike(f"%{search}%")
                )
            )

        # Execute query
        products = query.limit(50).all()

        # Generate AI captions efficiently using batch processing
        ai_captions = batch_ai_captions(products, generate_captions)

        # Build result efficiently
        result = []
        for i, p in enumerate(products):
            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": f"₹{p.price:,.0f}",
                "description": p.description,
                "rating": round(p.rating or 4.0, 1),
                "seller": p.shop.name if p.shop else "Independent Seller",
                "location": p.shop.location if p.shop else "Unknown",
                "image": resolve_product_image(p),
                "ai_caption": ai_captions[i],
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "products": result,
            "captions_generated": generate_captions,
            "user_role": "shop_manager" if generate_captions else "customer"
        }), 200

    except Exception as e:
        print("[Error - Get Products]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Single Product Details
@product_bp.route("/<int:product_id>", methods=["GET"])
@performance_monitor
def get_product_detail(product_id):
    """Fetch detailed product information with optional AI caption for Shop Managers only."""
    try:
        # Check if AI caption is requested and user has permission
        generate_captions = request.args.get("generate_captions", "false").lower() == "true"
        
        # Only allow AI caption generation for Shop Managers
        if generate_captions:
            from utils.auth_utils import get_current_user_from_token
            current_user = get_current_user_from_token()
            if not current_user or current_user.role not in ["shop_owner", "admin", "manager"]:
                generate_captions = False

        # Use joined query
        product = db.session.query(Product).join(Shop, Product.shop_id == Shop.id).filter(Product.id == product_id).first()
        
        if not product:
            return jsonify({"status": "error", "message": f"Product with id {product_id} not found."}), 404
        
        # Generate AI caption efficiently with caching
        caption = None
        if generate_captions:
            caption = cached_ai_caption(product.name, product.category or "Product", float(product.price))
        
        product_data = {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": f"₹{product.price:,.0f}",
            "description": product.description,
            "rating": round(product.rating or 4.0, 1),
            "badge": product.badge,
            "is_trending": product.is_trending,
            "is_active": product.is_active,
            "seller": product.shop.owner.full_name if product.shop and product.shop.owner else "Independent Seller",
            "shop_id": product.shop_id,
            "shop_location": product.shop.location if product.shop else "Unknown",
            "shop_city": product.shop.city if product.shop else "Unknown",
            "image": resolve_product_image(product),
            "ai_caption": caption,
        }
        
        return jsonify({
            "status": "success",
            "product": product_data,
            "captions_generated": generate_captions,
            "user_role": "shop_manager" if generate_captions else "customer"
        }), 200
        
    except Exception as e:
        print(f"[Error - Get Product {product_id}]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# AI-Driven Trending Product Recommendations
@product_bp.route("/suggested", methods=["GET"])
def get_suggested_products():
    """
    Suggest top products dynamically using Prophet trend analysis
    and Gemini AI captions.
    """
    try:
        # Load sales data for trend forecasting
        sales_data = SalesData.query.all()
        if not sales_data:
            # fallback to top-rated products if no data
            products = Product.query.order_by(Product.rating.desc()).limit(6).all()
            result = []
            for p in products:
                caption = generate_ai_caption(p.name, p.category or "Product", p.price)
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "price": f"₹{p.price:,.0f}",
                    "image": resolve_product_image(p),
                    "caption": caption
                })
            return jsonify({"status": "success", "source": "fallback", "suggested": result}), 200

        # Create DataFrame for Prophet analysis
        df = pd.DataFrame([{
            "Date": s.date,
            "Sales": s.revenue,
            "Product": s.product.name if s.product else "Unknown"
        } for s in sales_data])

        trending = top_trending_products(df, top_n=6)
        result = []

        for t in trending:
            product = Product.query.filter(Product.name.ilike(f"%{t['Product']}%")).first()
            if not product:
                continue
            caption = generate_ai_caption(product.name, product.category or "Product", product.price)
            result.append({
                "id": product.id,
                "name": product.name,
                "price": f"₹{product.price:,.0f}",
                "growth": f"{t['Growth']}%",
                "sales": f"₹{t['Sales_curr']:,.0f}",
                "image": resolve_product_image(product),
                "caption": caption
            })

        return jsonify({
            "status": "success",
            "source": "forecast",
            "suggested": result
        }), 200

    except Exception as e:
        print("[Error - Suggested Products]", e)
        return jsonify({"status": "error", "message": str(e)}), 500
