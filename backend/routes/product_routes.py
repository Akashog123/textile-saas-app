# backend/routes/products.py

from flask import Blueprint, jsonify, request
from models.model import db, Product, Shop, SalesData
from sqlalchemy import or_
from werkzeug.exceptions import NotFound
from services.ai_service import generate_ai_caption
from services.forecasting_service import top_trending_products
import pandas as pd

product_bp = Blueprint("product", __name__)

# GET: All Products (Dynamic + Filtered)
@product_bp.route("/", methods=["GET"])
def get_all_products():
    """
    Fetch all products dynamically with filtering and Gemini AI captions.
    Supports filters: category, price_min, price_max, search.
    """
    try:
        category = request.args.get("category")
        price_min = request.args.get("price_min", type=float)
        price_max = request.args.get("price_max", type=float)
        search = request.args.get("search")

        query = Product.query

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

        products = query.limit(50).all()
        result = []

        for p in products:
            shop = Shop.query.filter_by(id=p.shop_id).first()
            caption = generate_ai_caption(p.name, p.category or "Product", p.price)

            result.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": f"₹{p.price:,.0f}",
                "description": p.description,
                "rating": round(p.rating or 4.0, 1),
                "seller": shop.name if shop else "Independent Seller",
                "location": shop.location if shop else "Unknown",
                "image": p.image_url or f"https://picsum.photos/seed/{p.id}/800/600",
                "ai_caption": caption,
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "products": result
        }), 200

    except Exception as e:
        print("[Error - Get Products]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Single Product Details
@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product_detail(product_id):
    """Fetch detailed product information, including AI caption."""
    try:
        product = Product.query.get_or_404(product_id)
        shop = Shop.query.filter_by(id=product.shop_id).first()
        caption = generate_ai_caption(product.name, product.category or "Product", product.price)

        product_data = {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "price": f"₹{product.price:,.0f}",
            "rating": round(product.rating or 4.0, 1),
            "seller": shop.name if shop else "Independent Seller",
            "address": shop.location if shop else "N/A",
            "image": product.image_url or f"https://picsum.photos/seed/{product.id}/800/600",
            "ai_caption": caption,
        }

        return jsonify({
            "status": "success",
            "product": product_data
        }), 200

    except NotFound:
        return jsonify({
            "status": "error",
            "message": f"Product with id {product_id} not found."
        }), 404
    except Exception as e:
        print("[Error - Product Detail]", e)
        return jsonify({"status": "error", "message": "Failed to fetch product details."}), 500


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
                    "image": p.image_url or f"https://picsum.photos/seed/{p.id}/600/400",
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
                "image": product.image_url or f"https://picsum.photos/seed/{product.id}/600/400",
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
