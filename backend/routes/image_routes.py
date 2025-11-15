from flask import Blueprint, request, jsonify
import os
from PIL import Image
import numpy as np
import io
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

image_bp = Blueprint("images", __name__, url_prefix="/compare-images")

STORE_IMAGES_DIR = os.path.join(os.getcwd(), "data", "store_images")

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

    if not image_files:
        return jsonify({"error": "No images found"}), 404

    comparison_features = []
    valid_files = []

    for filename in image_files:
        with open(os.path.join(STORE_IMAGES_DIR, filename), "rb") as img_file:
            features = extract_image_features(img_file.read())
            comparison_features.append(features)
            valid_files.append(os.path.join("data", "store_images", filename))

    scaler = StandardScaler()
    all_scaled = scaler.fit_transform([input_features] + comparison_features)
    similarities = cosine_similarity([all_scaled[0]], all_scaled[1:])[0]

    best_index = int(np.argmax(similarities))

    return jsonify({
        "best_match_file": valid_files[best_index],
        "similarity_score": float(similarities[best_index])
    })
