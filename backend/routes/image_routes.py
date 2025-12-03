from flask import Blueprint, request, jsonify
import os
from PIL import Image
import numpy as np
import io
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from config import Config
import re
import pandas as pd
from models.model import ProductCatalog
from image_sim_embedding import build_image_embeddings, load_image_embeddings

def numeric_sort_key(filename):
    """Extract numbers from filename for correct number-wise sorting."""
    num = re.findall(r'\d+', filename)
    return int(num[0]) if num else 0
image_bp = Blueprint("images", __name__, url_prefix="/compare-images")

STORE_IMAGES_DIR = os.path.join(Config.BASE_DIR, "datasets","fashion-dataset", "images")
os.makedirs(STORE_IMAGES_DIR, exist_ok=True)

# Load pre-computed embeddings at startup
EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR = load_image_embeddings()
if EMBED_ARR.size == 0:
    # One-time build if embeddings don't exist
    print("Building image embeddings (first time)...")
    build_image_embeddings()
    EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR = load_image_embeddings()

def extract_image_features(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((48, 48))
    return np.array(img).flatten()

@image_bp.route('/', methods=['POST'])
def compare_images():
    global EMBED_IDS, EMBED_FILE_PATHS, EMBED_ARR

    if 'input_image' not in request.files:
        return jsonify({"error": "Send 'input_image' file"}), 400

    # Compute embedding for query image and normalize
    input_image = request.files['input_image'].read()
    q_emb = extract_image_features(input_image).astype('float32')
    q_norm = np.linalg.norm(q_emb)
    if q_norm > 0:
        q_emb = q_emb / q_norm

    # Check if embeddings are available
    if EMBED_ARR.size == 0:
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

    return jsonify({
        "status": "success",
        "total_matches": len(EMBED_IDS),
        "matches": matches
    }), 200
