# backend/routes/image_search_routes.py
"""
Image Search API Routes
Provides endpoint for customers to search products by uploading images.
Searches real shop products from the database.
"""

import os
from flask import Blueprint, request, jsonify
from services.product_image_search import (
    search_products_by_image,
    rebuild_product_image_index,
    get_image_search_status
)
from utils.response_helpers import success_response, error_response, handle_exceptions


image_search_bp = Blueprint('image_search', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@image_search_bp.route('/similar', methods=['POST'])
@handle_exceptions("Image Search")
def find_similar_products():
    """
    Find visually similar products from uploaded image.
    
    Form data:
    - image: Image file (required)
    - limit: Max results (default: 20)
    
    Returns products from shops sorted by visual similarity.
    """
    # Check if image was uploaded
    if 'image' not in request.files:
        return error_response("No image file provided. Send 'image' in form data.", 400)
    
    image_file = request.files['image']
    
    if image_file.filename == '':
        return error_response("No file selected", 400)
    
    if not allowed_file(image_file.filename):
        return error_response(
            f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", 
            400
        )
    
    # Check file size
    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return error_response(f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB", 400)
    
    # Get limit parameter
    try:
        limit = int(request.form.get('limit', 20))
    except (ValueError, TypeError):
        limit = 20
    
    # Perform search
    results = search_products_by_image(image_file, limit=limit)
    
    if 'error' in results:
        return error_response(results['error'], 500)
    
    return success_response(data=results)


@image_search_bp.route('/status', methods=['GET'])
@handle_exceptions("Image Search Status")
def image_search_status():
    """Get image search service status."""
    status = get_image_search_status()
    return success_response(data=status)


@image_search_bp.route('/rebuild', methods=['POST'])
@handle_exceptions("Rebuild Image Index")
def rebuild_index():
    """Rebuild image search index from product images."""
    result = rebuild_product_image_index()
    if result.get('success'):
        return success_response(
            data=result,
            message="Image index rebuilt successfully"
        )
    else:
        return error_response(result.get('message', 'Failed to rebuild index'), 500)
