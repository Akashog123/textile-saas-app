# routes/discovery_portal.py

from flask import Blueprint, jsonify, request
from models.model import db, Product, Shop, SalesData
from sqlalchemy import or_, func
from services.ai_service import generate_ai_caption
from config import Config
import requests
from decimal import Decimal

discovery_portal_bp = Blueprint("discovery_portal", __name__, url_prefix="/api/v1/customer")


# Helper: Geocode Shop Location (MapMyIndia)
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
        print("Geocoding error:", e)
    return None, None


# GET: Trending Fabrics (AI-enhanced captions)
@discovery_portal_bp.route("/trending-fabrics", methods=["GET"])
def get_trending_fabrics():
    """Return top trending fabrics with AI-generated marketing captions."""
    try:
        trending_fabrics = (
            db.session.query(
                Product,
                func.coalesce(func.sum(SalesData.revenue), 0).label("total_revenue"),
                func.coalesce(func.sum(SalesData.quantity_sold), 0).label("units_sold")
            )
            .outerjoin(SalesData, SalesData.product_id == Product.id)
            .group_by(Product.id)
            .order_by(func.coalesce(func.sum(SalesData.revenue), 0).desc(), Product.rating.desc())
            .limit(10)
            .all()
        )

        result = []

        for product, total_revenue, units_sold in trending_fabrics:
            price_value = _to_float(product.price)
            caption = generate_ai_caption(product.name, product.category or "Textile", price_value)
            result.append({
                "id": product.id,
                "name": product.name,
                "price": f"₹{price_value:,.0f}",
                "description": product.description or "",
                "rating": round(product.rating or 0, 1),
                "badge": product.badge or "Trending",
                "image": _resolve_product_image(product),
                "ai_caption": caption
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "fabrics": result
        }), 200

    except Exception as e:
        print("Error fetching trending fabrics:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to load trending fabrics.",
            "error": str(e)
        }), 500


def _to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _resolve_product_image(product):
    image = getattr(product, "image_url", None)
    if image:
        return image

    images_rel = getattr(product, "images", None)
    if images_rel is not None:
        try:
            first_image = images_rel.first()
        except AttributeError:
            first_image = images_rel[0] if images_rel else None
        if first_image and getattr(first_image, "url", None):
            return first_image.url

    if hasattr(product, "shop") and getattr(product.shop, "image_url", None):
        return product.shop.image_url

    return ""


# GET: Popular Shops
@discovery_portal_bp.route("/popular-shops", methods=["GET"])
def get_popular_shops():
    """Return popular shops with geolocation enrichment."""
    try:
        popular_shops = (
            db.session.query(
                Shop,
                func.coalesce(func.sum(SalesData.revenue), 0).label("total_revenue"),
                func.coalesce(func.sum(SalesData.quantity_sold), 0).label("units_sold")
            )
            .outerjoin(SalesData, SalesData.shop_id == Shop.id)
            .group_by(Shop.id)
            .order_by(func.coalesce(func.sum(SalesData.revenue), 0).desc(), Shop.rating.desc())
            .limit(10)
            .all()
        )

        results = []
        lat_lon_updated = False

        for shop, total_revenue, units_sold in popular_shops:
            if (shop.lat is None or shop.lon is None) and shop.location:
                lat, lon = geocode_address(shop.location)
                if lat is not None and lon is not None:
                    shop.lat, shop.lon = lat, lon
                    lat_lon_updated = True

            results.append({
                "id": shop.id,
                "name": shop.name,
                "description": shop.description or "",
                "rating": round(shop.rating or 0, 1),
                "location": shop.location or "",
                "lat": shop.lat,
                "lon": shop.lon,
                "image": shop.image_url or ""
            })

        if lat_lon_updated:
            db.session.commit()

        return jsonify({
            "status": "success",
            "count": len(results),
            "shops": results
        }), 200

    except Exception as e:
        print("Error fetching popular shops:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to fetch popular shops.",
            "error": str(e)
        }), 500


# GET: Nearby Shops (based on coordinates)
@discovery_portal_bp.route("/nearby-shops", methods=["GET"])
def get_nearby_shops():
    """Return shops located within a given radius from provided coordinates."""
    try:
        if not request.args.get("lat") or not request.args.get("lon"):
            return jsonify({
                "status": "error",
                "message": "Query parameters 'lat' and 'lon' are required.",
                "error": "missing_coordinates"
            }), 400

        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radius = float(request.args.get("radius", 0.25))

        nearby_shops = Shop.query.filter(
            Shop.lat.between(lat - radius, lat + radius),
            Shop.lon.between(lon - radius, lon + radius)
        ).limit(15).all()

        data = [{
            "id": s.id,
            "name": s.name,
            "rating": round(s.rating or 0, 1),
            "location": s.location or "",
            "lat": s.lat,
            "lon": s.lon,
            "image": s.image_url or ""
        } for s in nearby_shops]

        return jsonify({
            "status": "success",
            "count": len(data),
            "nearby_shops": data
        }), 200

    except Exception as e:
        print("Error fetching nearby shops:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to load nearby shops.",
            "error": str(e)
        }), 500


# GET: Search (Shops or Fabrics)
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
            "price": f"₹{_to_float(f.price):,.0f}",
            "image": f.image_url or ""
        } for f in fabrics]

        shop_results = [{
            "id": s.id,
            "name": s.name,
            "rating": round(s.rating or 0, 1),
            "location": s.location or "",
            "image": s.image_url or ""
        } for s in shops]

        return jsonify({
            "status": "success",
            "fabrics": fabric_results,
            "shops": shop_results
        }), 200

    except Exception as e:
        print("Error searching items:", e)
        return jsonify({
            "status": "error",
            "message": "Search operation failed.",
            "error": str(e)
        }), 500
