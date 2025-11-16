# routes/shop_explorer.py

from flask import Blueprint, jsonify, request
from models.model import db, Shop, Product
from config import Config
from services.ai_service import generate_ai_caption
import requests

shop_explorer_bp = Blueprint("shop_explorer", __name__, url_prefix="/api/v1/customer")


# GET: All Shops
@shop_explorer_bp.route("/shops", methods=["GET"])
def get_all_shops():
    """Fetch all registered shops with key summary details."""
    try:
        shops = Shop.query.all()
        result = []

        for s in shops:
            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description or "Trusted textile shop",
                "location": s.location or "N/A",
                "rating": round(s.rating or 4.2, 1),
                "is_popular": s.is_popular,
                "lat": s.lat,
                "lon": s.lon,
                "shortName": s.name.split()[0] if s.name else "Shop",
                "image": s.image_url or f"https://picsum.photos/seed/{s.id}/600/400",
            })

        return jsonify({"status": "success", "count": len(result), "shops": result}), 200

    except Exception as e:
        print("[Error - Get All Shops]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Single Shop Details (with Products)
@shop_explorer_bp.route("/shop/<int:shop_id>", methods=["GET"])
def get_shop_details(shop_id):
    """Fetch detailed shop info with all its listed fabrics."""
    try:
        shop = Shop.query.get_or_404(shop_id)
        products = Product.query.filter_by(shop_id=shop.id).all()

        product_data = []
        for p in products:
            caption = generate_ai_caption(p.name, p.category, p.price)
            product_data.append({
                "id": p.id,
                "name": p.name,
                "price": f"₹{p.price:,.0f}",
                "description": p.description or "Premium textile fabric.",
                "category": p.category,
                "rating": round(p.rating or 4.0, 1),
                "image": p.image_url or f"https://picsum.photos/seed/{p.id}/600/400",
                "ai_caption": caption
            })

        data = {
            "id": shop.id,
            "name": shop.name,
            "description": shop.description or "",
            "rating": round(shop.rating or 4.3, 1),
            "location": shop.location or "N/A",
            "image": shop.image_url or f"https://picsum.photos/seed/{shop.id}/600/400",
            "products": product_data
        }

        return jsonify({"status": "success", "shop": data}), 200

    except Exception as e:
        print("[Error - Shop Details]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Search Shops & Fabrics
@shop_explorer_bp.route("/search", methods=["GET"])
def search():
    """Search both shops and fabrics dynamically."""
    try:
        query = request.args.get("q", "").strip().lower()
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
            "rating": round(s.rating or 4.0, 1),
            "image": s.image_url
        } for s in shops]

        fabric_results = [{
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": f"₹{p.price:,.0f}",
            "image": p.image_url or f"https://picsum.photos/seed/{p.id}/600/400"
        } for p in products]

        return jsonify({
            "status": "success",
            "shops": shop_results,
            "products": fabric_results
        }), 200

    except Exception as e:
        print("[Error - Search]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Nearby Shops (MapMyIndia)
@shop_explorer_bp.route("/nearby-shops", methods=["GET"])
def nearby_shops():
    """Find nearby textile shops using MapMyIndia API."""
    try:
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        if not (lat and lon):
            return jsonify({"status": "error", "message": "Missing coordinates"}), 400

        url = "https://atlas.mapmyindia.com/api/places/nearby/json"
        headers = {"Authorization": f"Bearer {Config.MAPMYINDIA_KEY}"}
        params = {"keywords": "fabric,textile,shop", "refLocation": f"{lat},{lon}", "radius": 3000}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "MapMyIndia API error"}), 500

        data = response.json()
        shops = [{
            "name": place.get("placeName", "Fabric Shop"),
            "address": place.get("placeAddress", "Unknown"),
            "lat": place.get("latitude"),
            "lon": place.get("longitude"),
            "rating": 4.2,
            "shortName": place.get("placeName", "Shop")[:10],
        } for place in data.get("suggestedLocations", [])]

        return jsonify({
            "status": "success",
            "count": len(shops),
            "nearby_shops": shops
        }), 200

    except Exception as e:
        print("[Error - Nearby Shops]", e)
        return jsonify({"status": "error", "message": str(e)}), 500
