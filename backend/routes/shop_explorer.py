# routes/shop_explorer.py

from flask import Blueprint, jsonify, request
from models.model import db, Shop, Product, User
from config import Config
from utils.image_utils import resolve_product_image, resolve_shop_image
from utils.auth_utils import token_required
from services.ai_service import generate_ai_caption
import requests
from math import cos, radians
# add near the top of routes/shop_explorer.py
import logging
logger = logging.getLogger(__name__)

def _serialize_shop(shop):
    """
    Lightweight serializer for Shop model used by the public explorer endpoints.
    Keeps fields minimal and safe (wraps attribute access).
    """
    try:
        # products_count and reviews_count use relationship queries (lazy/dynamic assumed)
        try:
            products_count = shop.products.count() if hasattr(shop, "products") and hasattr(shop.products, "count") else (len(shop.products) if shop.products is not None else 0)
        except Exception:
            products_count = None

        try:
            reviews_count = shop.reviews.count() if hasattr(shop, "reviews") and hasattr(shop.reviews, "count") else (len(shop.reviews) if shop.reviews is not None else 0)
        except Exception:
            reviews_count = None

        owner = None
        try:
            if getattr(shop, "owner", None):
                owner = {
                    "id": getattr(shop.owner, "id", None),
                    "full_name": getattr(shop.owner, "full_name", None),
                    "username": getattr(shop.owner, "username", None)
                }
        except Exception:
            owner = None

        return {
            "id": getattr(shop, "id", None),
            "name": getattr(shop, "name", None),
            "description": getattr(shop, "description", "") or "",
            "address": getattr(shop, "location", None) or getattr(shop, "address", None) or "",
            "city": getattr(shop, "city", None),
            "state": getattr(shop, "state", None),
            "lat": float(getattr(shop, "lat", None)) if getattr(shop, "lat", None) is not None else None,
            "lon": float(getattr(shop, "lon", None)) if getattr(shop, "lon", None) is not None else None,
            "rating": round(getattr(shop, "rating", 4.0) or 4.0, 1),
            "is_popular": bool(getattr(shop, "is_popular", False)),
            "image": resolve_shop_image(shop) if 'resolve_shop_image' in globals() else getattr(shop, "image_url", None),
            "owner": owner,
            "products_count": products_count,
            "reviews_count": reviews_count,
            "created_at": getattr(shop, "created_at", None).isoformat() if getattr(shop, "created_at", None) else None,
        }
    except Exception:
        logger.exception("Failed to serialize shop %s", getattr(shop, "id", "n/a"))
        # return minimal safe shape so endpoints can still respond
        return {
            "id": getattr(shop, "id", None),
            "name": getattr(shop, "name", None),
            "description": "",
            "address": "",
            "lat": None,
            "lon": None,
            "rating": 4.0,
            "image": getattr(shop, "image_url", None)
        }

shop_explorer_bp = Blueprint("shop_explorer", __name__)


# GET: All Shops
@shop_explorer_bp.route("/shops", methods=["GET"])
def get_all_shops():
    try:
        
        shops = Shop.query.all()
        result = [_serialize_shop(s) for s in shops]
        return jsonify({"status": "success", "count": len(result), "shops": result}), 200
    except Exception:
        logger.exception("[Error - Get All Shops]")
        return jsonify({"status": "error", "message": "Failed to fetch shops"}), 500


# ------------------------------------------------------------------
# Single Shop details (public)
# ------------------------------------------------------------------
@shop_explorer_bp.route("/shop/<int:shop_id>", methods=["GET"])
def get_shop_details(shop_id):
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404

        products = Product.query.filter_by(shop_id=shop.id).all()
        product_data = []
        for product in products:
            try:
                price = float(product.price) if product.price is not None else 0.0
            except Exception:
                price = 0.0

            caption = ""
            try:
                caption = generate_ai_caption(product.name, product.category, price)
            except Exception:
                logger.exception("AI caption failed for product %s", getattr(product, "id", "n/a"))

            product_data.append({
                "id": product.id,
                "name": product.name,
                "price": f"₹{price:,.0f}",
                "description": product.description or "",
                "category": product.category,
                "rating": round(getattr(product, "rating", 4.0) or 4.0, 1),
                "seller": getattr(product, "seller").full_name if getattr(product, "seller", None) else "Independent Seller",
                "image": resolve_product_image(product),
                "ai_caption": caption
            })

        shop_data = _serialize_shop(shop)
        shop_data["products"] = product_data
        return jsonify({"status": "success", "shop": shop_data}), 200
    except Exception:
        logger.exception("[Error - Shop Details]")
        return jsonify({"status": "error", "message": "Failed to fetch shop details"}), 500


# ------------------------------------------------------------------
# Search (public)
# ------------------------------------------------------------------
@shop_explorer_bp.route("/search", methods=["GET"])
def search():
    try:
        query = (request.args.get("q") or "").strip()
        if not query:
            return jsonify({"status": "success", "shops": [], "products": []}), 200

        shops = Shop.query.filter(Shop.name.ilike(f"%{query}%")).all()
        products = Product.query.filter(
            (Product.name.ilike(f"%{query}%")) |
            (Product.category.ilike(f"%{query}%")) |
            (Product.description.ilike(f"%{query}%"))
        ).limit(30).all()

        shop_results = [{
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "rating": round(getattr(s, "rating", 4.0) or 4.0, 1),
            "image": getattr(s, "image_url", None)
        } for s in shops]

        fabric_results = [{
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": f"₹{(float(p.price) if p.price is not None else 0):,.0f}",
            "image": resolve_product_image(p)
        } for p in products]

        return jsonify({"status": "success", "shops": shop_results, "products": fabric_results}), 200
    except Exception:
        logger.exception("[Error - Search]")
        return jsonify({"status": "error", "message": "Search failed"}), 500


# ------------------------------------------------------------------
# Nearby shops (MapMyIndia or local fallback)
# ------------------------------------------------------------------
@shop_explorer_bp.route("/nearby-shops", methods=["GET"])
def nearby_shops():
    try:
        lat_raw = request.args.get("lat")
        lon_raw = request.args.get("lon")
        radius_raw = request.args.get("radius")

        if not (lat_raw and lon_raw):
            return jsonify({"status": "error", "message": "Missing coordinates"}), 400

        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
            radius_meters = float(radius_raw) if radius_raw else 3000.0
        except ValueError:
            return jsonify({"status": "error", "message": "Coordinates and radius must be numeric"}), 400

        api_results = []
        if getattr(Config, "MAPMYINDIA_KEY", None):
            url = "https://atlas.mapmyindia.com/api/places/nearby/json"
            headers = {"Authorization": f"Bearer {Config.MAPMYINDIA_KEY}"}
            params = {"keywords": "fabric,textile,shop", "refLocation": f"{lat},{lon}", "radius": int(radius_meters)}
            try:
                response = requests.get(url, headers=headers, params=params, timeout=4)
                if response.status_code == 200:
                    data = response.json()
                    api_results = [{
                        "name": place.get("placeName", "Fabric Shop"),
                        "address": place.get("placeAddress", "Unknown"),
                        "lat": place.get("latitude"),
                        "lon": place.get("longitude"),
                        "rating": 4.2,
                        "shortName": (place.get("placeName") or "Shop")[:10],
                    } for place in data.get("suggestedLocations", [])]
            except Exception:
                logger.exception("[MapMyIndia Nearby Shops]")

        if not api_results:
            nearby_shops = _query_local_nearby_shops(lat, lon, radius_meters)
            return jsonify({"status": "success", "count": len(nearby_shops), "nearby_shops": nearby_shops}), 200

        return jsonify({"status": "success", "count": len(api_results), "nearby_shops": api_results}), 200
    except Exception:
        logger.exception("[Error - Nearby Shops]")
        return jsonify({"status": "error", "message": "Failed to find nearby shops"}), 500


def _query_local_nearby_shops(lat: float, lon: float, radius_meters: float):
    radius_degrees_lat = radius_meters / 111_000.0
    radius_degrees_lon = radius_degrees_lat / max(cos(radians(lat)), 0.1)

    query = (
        Shop.query
        .filter(Shop.lat.isnot(None), Shop.lon.isnot(None))
        .filter(Shop.lat.between(lat - radius_degrees_lat, lat + radius_degrees_lat))
        .filter(Shop.lon.between(lon - radius_degrees_lon, lon + radius_degrees_lon))
        .order_by(Shop.rating.desc())
        .limit(20)
    )

    shops = []
    for shop in query.all():
        shops.append({
            "name": shop.name,
            "address": shop.location or shop.address or "Unknown",
            "lat": float(shop.lat) if shop.lat is not None else None,
            "lon": float(shop.lon) if shop.lon is not None else None,
            "rating": round(shop.rating or 4.0, 1),
            "shortName": (shop.name or "Shop")[:10],
        })

    return shops
