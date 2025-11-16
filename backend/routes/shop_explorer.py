# routes/shop_explorer.py

from flask import Blueprint, jsonify, request
from models.model import db, Shop, Product
from config import Config
from services.ai_service import generate_ai_caption
import requests
from math import cos, radians

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
        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop:
            return jsonify({
                "status": "error",
                "message": f"Shop with id {shop_id} not found"
            }), 404

        products = Product.query.filter_by(shop_id=shop.id).all()
        product_data = []

        for product in products:
            price = _to_float(product.price)
            caption = generate_ai_caption(product.name, product.category, price)
            product_data.append({
                "id": product.id,
                "name": product.name,
                "price": f"₹{price:,.0f}",
                "description": product.description or "Premium textile fabric.",
                "category": product.category,
                "rating": round(getattr(product, "rating", 4.0) or 4.0, 1),
                "image": _resolve_product_image(product),
                "ai_caption": caption
            })

        shop_data = {
            "id": shop.id,
            "name": shop.name,
            "description": shop.description or "",
            "rating": round(getattr(shop, "rating", 4.3) or 4.3, 1),
            "location": shop.location or "N/A",
            "image": shop.image_url or f"https://picsum.photos/seed/{shop.id}/600/400",
            "products": product_data
        }

        return jsonify({"status": "success", "shop": shop_data}), 200

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
            return jsonify({
                "status": "error",
                "message": "Coordinates and radius must be numeric"
            }), 400

        api_results = []
        if Config.MAPMYINDIA_KEY:
            url = "https://atlas.mapmyindia.com/api/places/nearby/json"
            headers = {"Authorization": f"Bearer {Config.MAPMYINDIA_KEY}"}
            params = {
                "keywords": "fabric,textile,shop",
                "refLocation": f"{lat},{lon}",
                "radius": int(radius_meters)
            }

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
                        "shortName": place.get("placeName", "Shop")[:10],
                    } for place in data.get("suggestedLocations", [])]
            except Exception as exc:
                print("[MapMyIndia Nearby Shops]", exc)

        if not api_results:
            nearby_shops = _query_local_nearby_shops(lat, lon, radius_meters)
            return jsonify({
                "status": "success",
                "count": len(nearby_shops),
                "nearby_shops": nearby_shops
            }), 200

        return jsonify({
            "status": "success",
            "count": len(api_results),
            "nearby_shops": api_results
        }), 200

    except Exception as e:
        print("[Error - Nearby Shops]", e)
        return jsonify({"status": "error", "message": str(e)}), 500


def _query_local_nearby_shops(lat: float, lon: float, radius_meters: float):
    # Convert meters to approximate degrees. Adjust longitude delta by latitude to reduce distortion.
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
            "lat": shop.lat,
            "lon": shop.lon,
            "rating": round(shop.rating or 4.0, 1),
            "shortName": (shop.name or "Shop")[:10],
        })

    return shops
