"""
Nearby Search API
Provides access to nearby shop searches using local database
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import math
import requests
from models.model import Shop

nearby_bp = Blueprint('nearby_search', __name__)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000 # Convert to meters

@nearby_bp.route('/api/nearby-shops', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)
def get_nearby_shops():
    """
    Get nearby textile/fabric shops using local database
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "radius": int (in meters, default 5000),
        "keywords": str (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        radius = data.get('radius', 5000) # Default 5km
        keywords = data.get('keywords')
        
        if user_lat is None or user_lon is None:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
            
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except (ValueError, TypeError):
             return jsonify({
                'success': False,
                'error': 'Invalid latitude or longitude format'
            }), 400

        # Query all shops with location data
        shops = Shop.query.filter(Shop.lat.isnot(None), Shop.lon.isnot(None)).all()
        
        nearby_shops = []
        
        for shop in shops:
            try:
                distance = haversine_distance(user_lat, user_lon, shop.lat, shop.lon)
                
                if distance <= radius:
                    # Filter by keywords if provided
                    if keywords:
                        keyword_list = [k.strip().lower() for k in keywords.split(',')]
                        shop_text = f"{shop.name} {shop.description or ''} {shop.address or ''}".lower()
                        if not any(k in shop_text for k in keyword_list):
                            continue
                            
                    nearby_shops.append({
                        "id": str(shop.id),
                        "name": shop.name,
                        "address": f"{shop.address}, {shop.city}, {shop.state}",
                        "distance": round(distance, 2),
                        "latitude": shop.lat,
                        "longitude": shop.lon,
                        "placeId": f"shop_{shop.id}",
                        "image_url": shop.get_primary_image_url(resolve=True),
                        "rating": shop.rating,
                        "is_popular": shop.is_popular
                    })
            except Exception as e:
                print(f"Error processing shop {shop.id}: {e}")
                continue
                
        # Sort by distance
        nearby_shops.sort(key=lambda x: x['distance'])
        
        return jsonify({
            "success": True,
            "data": {
                "shops": nearby_shops,
                "user_location": {
                    "latitude": user_lat,
                    "longitude": user_lon
                },
                "total_results": len(nearby_shops)
            }
        })

    except Exception as e:
        print(f"Error in nearby search: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nearby_bp.route('/api/v1/reverse-geocode', methods=['GET'])
@cross_origin(supports_credentials=True)
def reverse_geocode():
    """
    Reverse geocoding proxy for Nominatim (OpenStreetMap)
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({'error': 'Missing lat or lon parameters'}), 400
        
    try:
        # Nominatim requires a User-Agent
        headers = {
            'User-Agent': 'SE-Textile-App/1.0'
        }
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return jsonify(response.json())
    except Exception as e:
        print(f"[Reverse Geocode Error] {str(e)}")
        return jsonify({'error': str(e)}), 500
