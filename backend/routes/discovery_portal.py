# routes/discovery_portal.py

from flask import Blueprint, jsonify, request
from models.model import db, Product, Shop
from sqlalchemy import or_
from services.ai_service import generate_ai_caption
from config import Config
import requests

discovery_portal_bp = Blueprint("discovery_portal", __name__, url_prefix="/api/v1/customer")


# ───────────────────────────────────────────────
# 🗺️ Helper: Geocode Shop Location (MapMyIndia)
# ───────────────────────────────────────────────
def geocode_address(address):
    """Fetch latitude and longitude for a given address using MapMyIndia API."""
    try:
        if not Config.MAPMYINDIA_KEY:
            return None, None

        url = f"https://atlas.mapmyindia.com/api/places/geocode"
        params = {"address": address, "key": Config.MAPMYINDIA_KEY}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if "copResults" in data and data["copResults"]:
            coords = data["copResults"][0]["geocode"]
            return float(coords["lat"]), float(coords["lng"])
    except Exception as e:
        print("❌ Geocoding error:", e)
    return None, None


# ───────────────────────────────────────────────
# 🔝 GET: Trending Fabrics (AI-enhanced captions)
# ───────────────────────────────────────────────
@discovery_portal_bp.route("/trending-fabrics", methods=["GET"])
def get_trending_fabrics():
    """Return top trending fabrics with AI-generated marketing captions."""
    try:
        fabrics = Product.query.filter_by(is_trending=True).limit(10).all()
        result = []

        for f in fabrics:
            caption = generate_ai_caption(f.name, f.category or "Textile", f.price)
            result.append({
                "id": f.id,
                "name": f.name,
                "price": f"₹{f.price:,.0f}",
                "description": f.description or "Premium textile fabric.",
                "rating": round(f.rating or 4.3, 1),
                "badge": f.badge or "Trending",
                "image": f.image_url or f"https://picsum.photos/seed/{f.id}/600/400",
                "ai_caption": caption
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "fabrics": result
        }), 200

    except Exception as e:
        print("❌ Error fetching trending fabrics:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to load trending fabrics.",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# 🌟 GET: Popular Shops
# ───────────────────────────────────────────────
@discovery_portal_bp.route("/popular-shops", methods=["GET"])
def get_popular_shops():
    """Return popular shops with geolocation enrichment."""
    try:
        shops = Shop.query.filter_by(is_popular=True).limit(10).all()
        results = []

        for s in shops:
            if not s.lat or not s.lon:
                lat, lon = geocode_address(s.location)
                if lat and lon:
                    s.lat, s.lon = lat, lon
                    db.session.commit()

            results.append({
                "id": s.id,
                "name": s.name,
                "description": s.description or "Trusted textile retailer.",
                "rating": round(s.rating or 4.5, 1),
                "location": s.location or "N/A",
                "lat": s.lat,
                "lon": s.lon,
                "image": s.image_url or f"https://picsum.photos/seed/shop{s.id}/600/400"
            })

        return jsonify({
            "status": "success",
            "count": len(results),
            "shops": results
        }), 200

    except Exception as e:
        print("❌ Error fetching popular shops:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to fetch popular shops.",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# 📍 GET: Nearby Shops (based on coordinates)
# ───────────────────────────────────────────────
@discovery_portal_bp.route("/nearby-shops", methods=["GET"])
def get_nearby_shops():
    """Return shops located within a given radius from provided coordinates."""
    try:
        lat = float(request.args.get("lat", 12.9716))
        lon = float(request.args.get("lon", 77.5946))
        radius = float(request.args.get("radius", 0.2))  # 20km ≈ 0.2° lat/lon

        nearby_shops = Shop.query.filter(
            Shop.lat.between(lat - radius, lat + radius),
            Shop.lon.between(lon - radius, lon + radius)
        ).limit(15).all()

        data = [{
            "id": s.id,
            "name": s.name,
            "rating": round(s.rating or 4.0, 1),
            "location": s.location or "N/A",
            "lat": s.lat,
            "lon": s.lon,
            "image": s.image_url or f"https://picsum.photos/seed/nearby{s.id}/600/400"
        } for s in nearby_shops]

        return jsonify({
            "status": "success",
            "count": len(data),
            "nearby_shops": data
        }), 200

    except Exception as e:
        print("❌ Error fetching nearby shops:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to load nearby shops.",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# 🔍 GET: Search (Shops or Fabrics)
# ───────────────────────────────────────────────
@discovery_portal_bp.route("/search", methods=["GET"])
def search_items():
    """Search for fabrics or shops by keyword."""
    try:
        q = request.args.get("q", "").strip().lower()
        if not q:
            return jsonify({"status": "success", "fabrics": [], "shops": []}), 200

        fabrics = Product.query.filter(or_(
            Product.name.ilike(f"%{q}%"),
            Product.description.ilike(f"%{q}%")
        )).limit(10).all()

        shops = Shop.query.filter(or_(
            Shop.name.ilike(f"%{q}%"),
            Shop.description.ilike(f"%{q}%")
        )).limit(10).all()

        fabric_results = [{
            "id": f.id,
            "name": f.name,
            "price": f"₹{f.price:,.0f}",
            "image": f.image_url or f"https://picsum.photos/seed/{f.id}/600/400"
        } for f in fabrics]

        shop_results = [{
            "id": s.id,
            "name": s.name,
            "rating": round(s.rating or 4.0, 1),
            "location": s.location,
            "image": s.image_url or f"https://picsum.photos/seed/shop{s.id}/600/400"
        } for s in shops]

        return jsonify({
            "status": "success",
            "fabrics": fabric_results,
            "shops": shop_results
        }), 200

    except Exception as e:
        print("❌ Error searching items:", e)
        return jsonify({
            "status": "error",
            "message": "Search operation failed.",
            "error": str(e)
        }), 500
