# backend/routes/service_explorer.py

from flask import Blueprint, jsonify, request
from models.model import db, Service, User, Category
from sqlalchemy import or_
from services.ai_service import generate_ai_caption
from config import Config
import requests

service_explorer_bp = Blueprint("service_explorer", __name__, url_prefix="/api/v1/customer")

# GET: All Available Services (Filtered)
@service_explorer_bp.route("/services", methods=["GET"])
def get_all_services():
    """
    Fetch all available services dynamically with optional filters.
    Includes AI-generated captions for customer-facing presentation.
    """
    try:
        category = request.args.get("category")
        price_min = request.args.get("price_min", type=float)
        price_max = request.args.get("price_max", type=float)
        search = request.args.get("search")

        query = Service.query

        # Apply filters dynamically
        if category:
            query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))
        if price_min is not None:
            query = query.filter(Service.price >= price_min)
        if price_max is not None:
            query = query.filter(Service.price <= price_max)
        if search:
            query = query.filter(
                or_(
                    Service.name.ilike(f"%{search}%"),
                    Service.description.ilike(f"%{search}%"),
                    Category.name.ilike(f"%{search}%")
                )
            )

        services = query.all()
        service_list = []

        for s in services:
            # Find professionals who can perform this service
            professionals = User.query.filter_by(
                role="professional", category_id=s.category_id, approved=True
            ).limit(3).all()

            professional_names = [p.username for p in professionals] or ["Independent Provider"]
            caption = generate_ai_caption(s.name, s.category.name if s.category else "Service", s.price)

            service_list.append({
                "id": s.id,
                "name": s.name,
                "description": s.description or "Professional home service.",
                "price": f"₹{int(s.price)}",
                "rating": round(getattr(s, "rating", 4.0), 1),
                "category": s.category.name if s.category else "General",
                "providers": professional_names,
                "imageUrls": [
                    f"https://picsum.photos/seed/{s.id+1}/800/600",
                    f"https://picsum.photos/seed/{s.id+2}/800/600"
                ],
                "ai_caption": caption
            })

        return jsonify({
            "status": "success",
            "count": len(service_list),
            "services": service_list
        }), 200

    except Exception as e:
        print("Error fetching services:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to load services.",
            "error": str(e)
        }), 500


# GET: Nearby Professionals (MapMyIndia / Fallback)
@service_explorer_bp.route("/nearby-professionals", methods=["GET"])
def get_nearby_professionals():
    """
    Fetch professionals near a given latitude and longitude.
    Uses MapMyIndia API if available; falls back to local DB if not.
    """
    try:
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        if not (lat and lon):
            return jsonify({"status": "error", "message": "Missing coordinates"}), 400

        # MapMyIndia API Integration
        if Config.MAPMYINDIA_KEY:
            url = "https://atlas.mapmyindia.com/api/places/nearby/json"
            headers = {"Authorization": f"Bearer {Config.MAPMYINDIA_KEY}"}
            params = {
                "keywords": "cleaning,repair,tailor,plumbing,service",
                "refLocation": f"{lat},{lon}",
                "radius": 3000
            }

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                professionals = [{
                    "name": place.get("placeName", "Service Provider"),
                    "address": place.get("placeAddress", "Unknown"),
                    "lat": place.get("latitude"),
                    "lon": place.get("longitude"),
                    "rating": 4.3,
                    "shortName": place.get("placeName", "Pro")[:12],
                } for place in data.get("suggestedLocations", [])]

                return jsonify({
                    "status": "success",
                    "source": "mapmyindia",
                    "count": len(professionals),
                    "professionals": professionals
                }), 200
            else:
                print("⚠️ MapMyIndia API fallback triggered.")

        # Local Database Fallback
        local_pros = User.query.filter_by(role="professional", approved=True).limit(5).all()
        pros_data = [{
            "name": p.username,
            "address": p.address or "N/A",
            "pincode": p.pincode or "000000",
            "rating": round(getattr(p, "rating", 4.0), 1),
        } for p in local_pros]

        return jsonify({
            "status": "success",
            "source": "local",
            "count": len(pros_data),
            "professionals": pros_data
        }), 200

    except Exception as e:
        print("Error fetching nearby professionals:", e)
        return jsonify({
            "status": "error",
            "message": "Unable to fetch nearby professionals.",
            "error": str(e)
        }), 500
