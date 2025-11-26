"""
MapmyIndia Nearby Search API Proxy
Provides secure access to MapmyIndia Places API for nearby shop searches
"""

from flask import Blueprint, request, jsonify
import requests
import os
from functools import wraps
import time

nearby_bp = Blueprint('nearby_search', __name__)

# MapmyIndia API Configuration
MAPMYINDIA_API_KEY = os.getenv('MAPMYINDIA_API_KEY', '')
MAPMYINDIA_BASE_URL = 'https://apis.mappls.com/advancedmaps/v1'

# Rate limiting storage (simple in-memory, consider Redis for production)
request_timestamps = {}

def rate_limit(max_requests=10, window_seconds=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old timestamps
            if client_ip in request_timestamps:
                request_timestamps[client_ip] = [
                    ts for ts in request_timestamps[client_ip]
                    if current_time - ts < window_seconds
                ]
            else:
                request_timestamps[client_ip] = []
            
            # Check rate limit
            if len(request_timestamps[client_ip]) >= max_requests:
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            # Add current request
            request_timestamps[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


@nearby_bp.route('/api/nearby-shops', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def get_nearby_shops():
    """
    Get nearby textile/fabric shops using MapmyIndia API
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "radius": int (in meters, default 5000),
        "keywords": str (default "textile shop,fabric shop")
    }
    
    Returns:
    {
        "success": bool,
        "data": {
            "shops": [
                {
                    "id": str,
                    "name": str,
                    "address": str,
                    "distance": float (in meters),
                    "latitude": float,
                    "longitude": float,
                    "placeId": str
                }
            ],
            "user_location": {
                "latitude": float,
                "longitude": float
            },
            "total_results": int
        },
        "error": str (if success is False)
    }
    """
    try:
        # Validate API key
        if not MAPMYINDIA_API_KEY:
            return jsonify({
                'success': False,
                'error': 'MapmyIndia API key not configured'
            }), 500
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required parameters
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'error': 'latitude and longitude are required'
            }), 400
        
        # Validate coordinate ranges
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            
            if not (-90 <= latitude <= 90):
                raise ValueError('Latitude must be between -90 and 90')
            if not (-180 <= longitude <= 180):
                raise ValueError('Longitude must be between -180 and 180')
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid coordinates: {str(e)}'
            }), 400
        
        # Optional parameters
        radius = data.get('radius', 5000)  # Default 5km
        keywords = data.get('keywords', 'textile shop;fabric shop;cloth shop')
        
        # Validate radius
        try:
            radius = int(radius)
            if radius < 100 or radius > 50000:  # 100m to 50km
                radius = 5000
        except (ValueError, TypeError):
            radius = 5000
        
        # Call MapmyIndia Nearby API
        nearby_url = f'{MAPMYINDIA_BASE_URL}/{MAPMYINDIA_API_KEY}/nearby/json'
        
        params = {
            'keywords': keywords,
            'refLocation': f'{latitude},{longitude}',
            'radius': radius,
            'page': 1
        }
        
        print(f"[Nearby Search] Calling MapmyIndia API for location: {latitude}, {longitude}")
        
        response = requests.get(nearby_url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"[Nearby Search Error] Status: {response.status_code}, Response: {response.text}")
            return jsonify({
                'success': False,
                'error': f'MapmyIndia API error: {response.status_code}'
            }), 502
        
        api_data = response.json()
        
        # Transform MapmyIndia response to our format
        shops = []
        
        if 'suggestedLocations' in api_data:
            for location in api_data['suggestedLocations']:
                shop = {
                    'id': location.get('eLoc', location.get('placeName', str(len(shops)))),
                    'name': location.get('placeName', 'Unknown Shop'),
                    'address': location.get('placeAddress', location.get('address', 'Address not available')),
                    'distance': location.get('distance', 0),
                    'latitude': location.get('latitude', location.get('lat', 0)),
                    'longitude': location.get('longitude', location.get('lng', 0)),
                    'placeId': location.get('eLoc', ''),
                    'type': location.get('type', 'shop'),
                    'category': location.get('keywords', [])
                }
                shops.append(shop)
        
        result = {
            'success': True,
            'data': {
                'shops': shops,
                'user_location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'total_results': len(shops),
                'search_radius': radius
            }
        }
        
        print(f"[Nearby Search] Found {len(shops)} shops")
        
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request to MapmyIndia API timed out'
        }), 504
        
    except requests.exceptions.RequestException as e:
        print(f"[Nearby Search Error] Request exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to connect to MapmyIndia API'
        }), 502
        
    except Exception as e:
        print(f"[Nearby Search Error] Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
