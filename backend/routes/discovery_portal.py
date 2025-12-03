# routes/discovery_portal.py

from flask import Blueprint, jsonify, request
from models.model import db, Product, Shop, SalesData
from sqlalchemy import or_, func
from utils.image_utils import resolve_product_image, resolve_shop_image
from utils.performance_utils import batch_ai_captions, performance_monitor
from config import Config
import requests
from decimal import Decimal

discovery_portal_bp = Blueprint("discovery_portal", __name__)


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
@performance_monitor
def get_trending_fabrics():
    """Return top trending fabrics with AI-generated marketing captions for Shop Managers only."""
    try:
        # Check if AI captions are requested and user has permission
        generate_captions = request.args.get("generate_captions", "false").lower() == "true"
        
        # Only allow AI caption generation for Shop Managers
        if generate_captions:
            from utils.auth_utils import extract_token_from_request, decode_jwt
            from models.model import User
            
            token = extract_token_from_request()
            if not token:
                generate_captions = False
            else:
                decoded = decode_jwt(token)
                if decoded:
                    user = User.query.get(decoded.get("user_id"))
                    if not user or user.role not in ["shop_owner", "admin", "manager"]:
                        generate_captions = False  # Deny AI generation for regular customers
                else:
                    generate_captions = False
        
        # Use a single session with proper cleanup
        with db.session.begin():
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

        # Extract products for batch AI caption generation
        products = [product for product, _, _ in trending_fabrics]
        
        # Generate AI captions efficiently using batch processing
        ai_captions = batch_ai_captions(products, generate_captions)

        # Build result efficiently
        result = []
        for i, (product, total_revenue, units_sold) in enumerate(trending_fabrics):
            price_value = _to_float(product.price)
            
            result.append({
                "id": product.id,
                "name": product.name,
                "price": f"₹{price_value:,.0f}",
                "description": product.description or "",
                "rating": round(product.rating or 0, 1),
                "badge": product.badge or "Trending",
                "image": resolve_product_image(product),
                "ai_caption": ai_captions[i]
            })

        return jsonify({
            "status": "success",
            "count": len(result),
            "fabrics": result,
            "captions_generated": generate_captions,
            "user_role": "shop_manager" if generate_captions else "customer"
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


# GET: Popular Shops
@discovery_portal_bp.route("/popular-shops", methods=["GET"])
@performance_monitor
def get_popular_shops():
    """Return popular shops with geolocation enrichment."""
    try:
        # Use a single session with proper cleanup
        with db.session.begin():
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
        shops_to_update = []

        # Process shops outside of database session
        for shop, total_revenue, units_sold in popular_shops:
            # Check if geocoding is needed
            if (shop.lat is None or shop.lon is None) and shop.location:
                lat, lon = geocode_address(shop.location)
                if lat is not None and lon is not None:
                    shops_to_update.append({"id": shop.id, "lat": lat, "lon": lon})
                    shop.lat, shop.lon = lat, lon

            results.append({
                "id": shop.id,
                "name": shop.name,
                "description": shop.description or "",
                "rating": round(shop.rating or 0, 1),
                "location": shop.location or "",
                "lat": shop.lat,
                "lon": shop.lon,
                "image": resolve_shop_image(shop)
            })

        # Batch update geocoded shops if any
        if shops_to_update:
            try:
                with db.session.begin():
                    for update in shops_to_update:
                        db.session.query(Shop).filter(Shop.id == update["id"]).update({
                            "lat": update["lat"],
                            "lon": update["lon"]
                        })
            except Exception as e:
                print(f"Failed to update shop geocodes: {e}")

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
            "image": resolve_shop_image(s)
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
            "description": f.description or "",
            "category": f.category or "General",
            "rating": f.rating or 4.0,
            "seller": f.seller.full_name if f.seller else "Independent Seller",
            "image": resolve_product_image(f)
        } for f in fabrics]

        shop_results = [{
            "id": s.id,
            "name": s.name,
            "rating": round(s.rating or 0, 1),
            "location": s.location or "",
            "image": resolve_shop_image(s)
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
