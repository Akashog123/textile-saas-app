"""
Image routes for photo search for similar fabrics
Allows customers to search nearby textile shops using a photo
and get visually similar results within 5 seconds.
"""

from flask import Blueprint, request, jsonify
import os
import time
from PIL import Image
import numpy as np
import io
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from config import Config
import re
import pandas as pd
from models.model import db, Product, Shop, ProductImage, ProductCatalog

try:
    from image_sim_embedding import build_image_embeddings, load_image_embeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("[Image Routes] image_sim_embedding module not available, using fallback similarity")

def numeric_sort_key(filename):
    """Extract numbers from filename for correct number-wise sorting."""
    num = re.findall(r'\d+', filename)
    return int(num[0]) if num else 0

image_bp = Blueprint("images", __name__, url_prefix="/compare-images")

STORE_IMAGES_DIR = os.path.join(Config.BASE_DIR, "datasets","fashion-dataset", "images")
os.makedirs(STORE_IMAGES_DIR, exist_ok=True)

# SLA: 5 seconds for image search
IMAGE_SEARCH_SLA_MS = 5000

# Load pre-computed embeddings at startup (if available)
EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR = [], [], np.array([])
if EMBEDDINGS_AVAILABLE:
    try:
        EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR = load_image_embeddings()
        if EMBED_ARR.size == 0:
            # One-time build if embeddings don't exist
            print("Building image embeddings (first time)...")
            build_image_embeddings()
            EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR = load_image_embeddings()
    except Exception as e:
        print(f"[Image Routes] Could not load embeddings: {e}")


def extract_image_features(img_bytes):
    """Extract color histogram and basic features from image."""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((48, 48))
    return np.array(img).flatten()


def extract_color_histogram(img_bytes):
    """Extract color histogram for better fabric matching."""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((64, 64))
    
    # Calculate color histogram for each channel
    r, g, b = img.split()
    r_hist = np.histogram(np.array(r), bins=32, range=(0, 256))[0]
    g_hist = np.histogram(np.array(g), bins=32, range=(0, 256))[0]
    b_hist = np.histogram(np.array(b), bins=32, range=(0, 256))[0]
    
    # Normalize and concatenate
    histogram = np.concatenate([r_hist, g_hist, b_hist]).astype(float)
    histogram = histogram / (histogram.sum() + 1e-7)
    return histogram


@image_bp.route('/', methods=['POST'])
def compare_images():
    """Compare input image against store images using pre-computed embeddings."""
    global EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR
    start_time = time.perf_counter()

    if 'input_image' not in request.files:
        return jsonify({"error": "Send 'input_image' file"}), 400

    # Compute embedding for query image and normalize
    input_image = request.files['input_image'].read()
    q_emb = extract_image_features(input_image).astype('float32')
    q_norm = np.linalg.norm(q_emb)
    if q_norm > 0:
        q_emb = q_emb / q_norm

    # Check if embeddings are available
    if not isinstance(EMBED_ARR, np.ndarray) or EMBED_ARR.size == 0:
        return jsonify({"error": "Embeddings not available. Please run build_image_embeddings()"}), 500

    # Compute cosine similarity via dot product (embeddings are L2-normalized)
    similarities = (EMBED_ARR @ q_emb).astype('float32')

    # Get top 10 matches
    top_k = 10
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Load catalog for product details
    catalog_path = os.path.join(Config.BASE_DIR, "datasets", "fashion-dataset", "catalog.csv")
    try:
        catalog_df = pd.read_csv(catalog_path)
        catalog_dict = {}
        for _, row in catalog_df.iterrows():
            product_id = str(row['product_id'])
            catalog_dict[product_id] = {
                'product_name': row['product_name'],
                'category': row['category'],
                'subcategory': row['subcategory'],
                'article_type': row['article_type'],
                'color': row['color'],
                'gender': row['gender']
            }
    except Exception as e:
        print(f"Error loading catalog: {e}")
        catalog_dict = {}
    
    # Load prices from ProductCatalog database
    try:
        price_items = ProductCatalog.query.all()
        price_dict = {}
        for item in price_items:
            price_dict[item.product_id] = item.price
    except Exception as e:
        print(f"Error loading prices from database: {e}")
        price_dict = {}

    # Build matches from top indices
    matches = []
    for idx in top_indices:
        product_id = EMBED_IDS[idx]
        file_path = EMBED_FILE_PATHS[idx]
        sim_score = float(similarities[idx])

        product_info = catalog_dict.get(product_id, {})

        matches.append({
            "file": file_path,
            "similarity_score": sim_score,
            "product_id": product_id,
            "product_name": product_info.get('product_name', f"Product {product_id}"),
            "category": product_info.get('category', 'Unknown'),
            "subcategory": product_info.get('subcategory', 'Unknown'),
            "color": product_info.get('color', 'Unknown'),
            "gender": product_info.get('gender', 'Unisex'),
            "article_type": product_info.get('article_type', 'Unknown'),
            "price": price_dict.get(product_id, None)
        })

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    return jsonify({
        "status": "success",
        "total_matches": len(EMBED_IDS) if EMBED_IDS else 0,
        "matches": matches,
        "duration_ms": duration_ms,
        "sla_met": duration_ms <= IMAGE_SEARCH_SLA_MS
    }), 200


@image_bp.route('/search-products', methods=['POST'])
def search_similar_products():
    """
    Search for visually similar products/fabrics.
    Returns matching products from shops within 5 seconds SLA.
    """
    start_time = time.perf_counter()
    
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Send 'image' file"}), 400
    
    try:
        input_image = request.files['image'].read()
        input_histogram = extract_color_histogram(input_image)
        
        # Get location params for nearby filtering (optional)
        lat = request.form.get('lat', type=float)
        lon = request.form.get('lon', type=float)
        radius_km = request.form.get('radius_km', default=10.0, type=float)
        limit = request.form.get('limit', default=10, type=int)
        limit = min(limit, 20)  # Cap at 20 results
        
        # Query products with images
        products_with_images = db.session.query(Product, ProductImage).join(
            ProductImage, Product.id == ProductImage.product_id
        ).filter(
            Product.is_active == True
        ).limit(100).all()  # Limit for performance
        
        if not products_with_images:
            return jsonify({
                "status": "success",
                "message": "No products with images found",
                "products": [],
                "duration_ms": int((time.perf_counter() - start_time) * 1000)
            }), 200
        
        # Calculate similarity scores
        similar_products = []
        
        for product, product_image in products_with_images:
            try:
                # Try to load product image
                image_path = None
                if product_image.url.startswith('http'):
                    # Skip remote URLs for now (would need async fetch)
                    continue
                else:
                    # Local image path
                    if product_image.url.startswith('/'):
                        image_path = os.path.join(Config.BASE_DIR, product_image.url.lstrip('/'))
                    else:
                        image_path = os.path.join(Config.UPLOAD_FOLDER, product_image.url)
                
                if not image_path or not os.path.exists(image_path):
                    continue
                
                with open(image_path, 'rb') as f:
                    product_histogram = extract_color_histogram(f.read())
                
                # Calculate cosine similarity
                similarity = float(cosine_similarity([input_histogram], [product_histogram])[0][0])
                
                if similarity > 0.5:  # Threshold for relevance
                    similar_products.append({
                        "product_id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "price": f"₹{float(product.price):,.0f}",
                        "image_url": product_image.url,
                        "similarity_score": round(similarity, 3),
                        "shop_id": product.shop_id,
                        "shop_name": product.shop.name if product.shop else "Unknown"
                    })
            except Exception as e:
                print(f"[Image Search] Error processing product {product.id}: {e}")
                continue
        
        # Sort by similarity and limit
        similar_products.sort(key=lambda x: x['similarity_score'], reverse=True)
        similar_products = similar_products[:limit]
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return jsonify({
            "status": "success",
            "count": len(similar_products),
            "products": similar_products,
            "duration_ms": duration_ms,
            "sla_met": duration_ms <= IMAGE_SEARCH_SLA_MS,
            "sla_limit_ms": IMAGE_SEARCH_SLA_MS
        }), 200
        
    except Exception as e:
        print(f"[Image Search Error] {e}")
        return jsonify({
            "status": "error",
            "message": "Image search failed",
            "error": str(e)
        }), 500


@image_bp.route('/search-shops', methods=['POST'])
def search_shops_by_image():
    """
    Find nearby shops with similar fabric/products.
    Uses image similarity + location for best results.
    """
    start_time = time.perf_counter()
    
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "Send 'image' file"}), 400
    
    try:
        input_image = request.files['image'].read()
        input_histogram = extract_color_histogram(input_image)
        
        # Location params
        lat = request.form.get('lat', type=float)
        lon = request.form.get('lon', type=float)
        radius_km = request.form.get('radius_km', default=10.0, type=float)
        
        # Get shops with products that have images
        shop_query = db.session.query(Shop).filter(Shop.lat.isnot(None), Shop.lon.isnot(None))
        
        # Filter by location if provided
        if lat and lon:
            # Approximate degree-to-km conversion
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(np.cos(np.radians(lat))))
            
            shop_query = shop_query.filter(
                Shop.lat.between(lat - lat_range, lat + lat_range),
                Shop.lon.between(lon - lon_range, lon + lon_range)
            )
        
        shops = shop_query.limit(20).all()
        
        shop_results = []
        for shop in shops:
            # Get shop's products with images
            products = Product.query.filter_by(shop_id=shop.id, is_active=True).limit(10).all()
            
            max_similarity = 0
            matching_product = None
            
            for product in products:
                product_image = product.images.first() if hasattr(product, 'images') else None
                if not product_image:
                    continue
                
                try:
                    image_path = None
                    if not product_image.url.startswith('http'):
                        if product_image.url.startswith('/'):
                            image_path = os.path.join(Config.BASE_DIR, product_image.url.lstrip('/'))
                        else:
                            image_path = os.path.join(Config.UPLOAD_FOLDER, product_image.url)
                    
                    if not image_path or not os.path.exists(image_path):
                        continue
                    
                    with open(image_path, 'rb') as f:
                        product_histogram = extract_color_histogram(f.read())
                    
                    similarity = float(cosine_similarity([input_histogram], [product_histogram])[0][0])
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                        matching_product = product
                        
                except Exception:
                    continue
            
            if max_similarity > 0.4:  # Threshold
                shop_results.append({
                    "shop_id": shop.id,
                    "name": shop.name,
                    "address": shop.address or shop.location,
                    "city": shop.city,
                    "lat": float(shop.lat) if shop.lat else None,
                    "lon": float(shop.lon) if shop.lon else None,
                    "rating": round(shop.rating or 4.0, 1),
                    "similarity_score": round(max_similarity, 3),
                    "matching_product": {
                        "id": matching_product.id,
                        "name": matching_product.name,
                        "price": f"₹{float(matching_product.price):,.0f}"
                    } if matching_product else None
                })
        
        # Sort by similarity
        shop_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return jsonify({
            "status": "success",
            "count": len(shop_results),
            "shops": shop_results,
            "duration_ms": duration_ms,
            "sla_met": duration_ms <= IMAGE_SEARCH_SLA_MS,
            "sla_limit_ms": IMAGE_SEARCH_SLA_MS
        }), 200
        
    except Exception as e:
        print(f"[Shop Image Search Error] {e}")
        return jsonify({
            "status": "error",
            "message": "Shop search failed",
            "error": str(e)
        }), 500
