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

def numeric_sort_key(filename):
    """Extract numbers from filename for correct number-wise sorting."""
    num = re.findall(r'\d+', filename)
    return int(num[0]) if num else 0
image_bp = Blueprint("images", __name__, url_prefix="/compare-images")

STORE_IMAGES_DIR = os.path.join(Config.BASE_DIR, "datasets","fashion-dataset", "images")
os.makedirs(STORE_IMAGES_DIR, exist_ok=True)

def extract_image_features(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((48, 48))
    return np.array(img).flatten()

@image_bp.route('/', methods=['POST'])
def compare_images():

    if 'input_image' not in request.files:
        return jsonify({"error": "Send 'input_image' file"}), 400

    input_image = request.files['input_image'].read()
    input_features = extract_image_features(input_image)

    image_files = [
        f for f in os.listdir(STORE_IMAGES_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    image_files = sorted(image_files, key=numeric_sort_key)[:1000]
    print(image_files)
    if not image_files:
        return jsonify({"error": "No images found"}), 404

    # Load catalog for product details
    catalog_path = os.path.join(Config.BASE_DIR, "datasets", "fashion-dataset", "catalog.csv")
    try:
        catalog_df = pd.read_csv(catalog_path)
        catalog_dict = {}
        for _, row in catalog_df.iterrows():
            product_id = row['product_id']
            catalog_dict[str(product_id)] = {
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

    comparison_features = []
    valid_files = []

    for filename in image_files:
        with open(os.path.join(STORE_IMAGES_DIR, filename), "rb") as img_file:
            features = extract_image_features(img_file.read())
            comparison_features.append(features)
            valid_files.append(os.path.join("datasets", "fashion-dataset", "images", filename))

    scaler = StandardScaler()
    all_scaled = scaler.fit_transform([input_features] + comparison_features)
    similarities = cosine_similarity([all_scaled[0]], all_scaled[1:])[0]

    # Get top 10 matches
    top_indices = np.argsort(similarities)[::-1][:10]
    
    matches = []
    for idx in top_indices:
        file_path = valid_files[idx]
        filename = os.path.basename(file_path).split('.')[0]  # Get product_id from filename
        
        # Get product details from catalog
        product_info = catalog_dict.get(filename, {})
        
        matches.append({
            "file": file_path,
            "similarity_score": float(similarities[idx]),
            "product_id": filename,
            "product_name": product_info.get('product_name', f"Product {filename}"),
            "category": product_info.get('category', 'Unknown'),
            "subcategory": product_info.get('subcategory', 'Unknown'),
            "color": product_info.get('color', 'Unknown'),
            "gender": product_info.get('gender', 'Unisex'),
            "article_type": product_info.get('article_type', 'Unknown'),
            "price": price_dict.get(filename, None)
        })

    return jsonify({
        "status": "success",
        "total_matches": len(image_files),
        "matches": matches
    }), 200
