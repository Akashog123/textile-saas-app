import os
import pandas as pd
import requests
import time
import random
import traceback
from datetime import datetime
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from utils.auth_utils import token_required, roles_required
from utils.validation import validate_file_upload
from services.ai_service import generate_ai_caption, forecast_trends, generate_marketing_poster, batch_generate_posters
from models.model import db, MarketingHistory

# Blueprint Setup
marketing_bp = Blueprint("marketing", __name__)

UPLOAD_FOLDER = "./uploads/marketing"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg"}


# Helper: File Validation
def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Helper: Download image from URL
def download_image_from_url(url: str, filename: str) -> str:
    """Download image from URL and save locally."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f"Failed to download image from URL {url}: {e}")
        return None


def _get_generation_method(prompt: str, poster_path: str) -> str:
    """Determine the generation method used for the poster."""
    if not poster_path:
        return "failed"
    elif prompt and "fashion product marketing poster" in prompt:
        return "text_based"  # Used fallback prompt
    else:
        return "ai_context"  # Used context-based or optimized prompt


# Global progress tracking
import threading
progress_lock = threading.Lock()
generation_progress = {
    "status": "idle",
    "current_step": "",
    "current_item": 0,
    "total_items": 0,
    "batch_progress": 0,
    "total_batches": 0,
    "errors": [],
    "start_time": None
}


def update_progress(status: str, current_step: str = "", current_item: int = 0, total_items: int = 0, error: str = None):
    """Update global progress state."""
    global generation_progress
    with progress_lock:
        generation_progress.update({
            "status": status,
            "current_step": current_step,
            "current_item": current_item,
            "total_items": total_items,
            "errors": generation_progress["errors"] + [error] if error else generation_progress["errors"]
        })


def _reset_progress_internal():
    """Internal function to reset generation progress."""
    global generation_progress
    with progress_lock:
        generation_progress = {
            "status": "idle",
            "current_step": "",
            "current_item": 0,
            "total_items": 0,
            "batch_progress": 0,
            "total_batches": 0,
            "errors": [],
            "start_time": None
        }


# GET: Get generation progress
@marketing_bp.route("/progress", methods=["GET"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def get_generation_progress(current_user):
    """Get real-time progress of marketing content generation."""
    global generation_progress
    with progress_lock:
        # Calculate elapsed time
        elapsed_time = None
        if generation_progress["start_time"]:
            elapsed_time = time.time() - generation_progress["start_time"]
        
        return jsonify({
            "status": generation_progress["status"],
            "current_step": generation_progress["current_step"],
            "current_item": generation_progress["current_item"],
            "total_items": generation_progress["total_items"],
            "batch_progress": generation_progress["batch_progress"],
            "total_batches": generation_progress["total_batches"],
            "progress_percentage": min(100, (generation_progress["current_item"] / max(1, generation_progress["total_items"])) * 100) if generation_progress["total_items"] > 0 else 0,
            "errors": generation_progress["errors"][-5:],  # Return last 5 errors
            "elapsed_time": elapsed_time
        })


# POST: Reset progress
@marketing_bp.route("/progress/reset", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def reset_progress(current_user):
    """Reset generation progress."""
    _reset_progress_internal()
    return jsonify({"status": "success", "message": "Progress reset"})


def _process_csv_with_robust_batching(df: pd.DataFrame, filename: str, aspect_ratio: str = "", batch_size: int = 3) -> tuple[list, list]:
    """Process CSV with robust batch processing, exponential backoff retry logic, and progress tracking."""
    global generation_progress
    
    ai_captions = []
    downloaded_images = []
    product_names = []
    
    # Initialize progress
    update_progress("processing", "Starting CSV processing", 0, len(df))
    generation_progress["start_time"] = time.time()
    
    print(f"[MARKETING] Starting robust batch processing for {len(df)} rows")
    print(f"[MARKETING] Settings: aspect_ratio={aspect_ratio}, batch_size={batch_size}")
    
    # First pass: Download images and generate captions
    for idx, (_, row) in enumerate(df.head(5).iterrows()):
        product = row.get("ProductName", "Fabric")
        category = row.get("Category", "Textile")
        price = row.get("Price", 1000)
        description = row.get("Description", "")
        image_url = row.get("ImageURL", "")
        
        product_names.append(product)
        
        # Update progress
        update_progress("processing", f"Processing product {idx+1}: {product}", idx, len(df))
        
        print(f"[MARKETING] Processing product {idx+1}/{len(df)}: {product}")
        
        # Download image if URL provided with retry logic
        image_path = None
        if image_url and str(image_url).strip():
            image_filename = f"product_{idx}_{secure_filename(filename.split('.')[0])}.jpg"
            update_progress("processing", f"Downloading image for {product}", idx, len(df))
            image_path = _download_image_with_retry(image_url, image_filename, max_retries=3)
            if image_path:
                downloaded_images.append(image_path)
                print(f"[MARKETING] Downloaded image: {image_filename}")
        
        # Generate caption with retry logic
        update_progress("processing", f"Generating caption for {product}", idx, len(df))
        caption = _generate_caption_with_retry(product, category, price, image_path, description, max_retries=2)
        
        ai_captions.append({
            "product": product,
            "category": category,
            "price": price,
            "description": description,
            "image_url": image_url,
            "caption": caption,
            "has_image": bool(image_path),
            "image_path": image_path
        })
    
    # Second pass: Generate posters for downloaded images with robust batch processing
    if downloaded_images:
        total_batches = (len(downloaded_images) + batch_size - 1) // batch_size
        generation_progress["total_batches"] = total_batches
        
        print(f"[MARKETING] Starting robust AI poster generation for {len(downloaded_images)} images...")
        update_progress("generating_posters", "Starting poster generation", 0, len(downloaded_images))
        
        poster_results = _batch_generate_posters_with_retry(
            downloaded_images, 
            product_names[:len(downloaded_images)], 
            aspect_ratio=aspect_ratio,
            batch_size=batch_size,
            max_retries=3
        )
        
        # Add poster information to captions
        for i, poster_result in enumerate(poster_results):
            if poster_result['success'] and i < len(ai_captions):
                # Convert poster file path to URL for frontend
                poster_file_path = poster_result['poster_path']
                poster_url = f"/uploads/marketing/{os.path.basename(poster_file_path)}" if poster_file_path else None
                
                ai_captions[i]['poster_path'] = poster_url  # Use URL instead of file path
                ai_captions[i]['poster_prompt'] = poster_result['prompt']
                ai_captions[i]['generation_method'] = _get_generation_method(
                    poster_result['prompt'], poster_result['poster_path']
                )
                print(f"[MARKETING] Poster generated for {ai_captions[i]['product']}")
            else:
                print(f"[MARKETING] Poster failed for {ai_captions[i]['product']}: {poster_result.get('error', 'Unknown error')}")
    
    # Final progress update
    update_progress("completed", "Processing completed", len(df), len(df))
    
    return ai_captions, []  # Return tuple: (ai_captions, trend_data)


def _download_image_with_retry(url: str, filename: str, max_retries: int = 3) -> str:
    """Download image with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"[MARKETING] Image download attempt {attempt + 1}/{max_retries}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"[MARKETING] Image downloaded successfully: {filename}")
            return filepath
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"[MARKETING] Download failed: {e}. Retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
            else:
                print(f"[MARKETING] Image download failed after {max_retries} attempts: {e}")
                return None


def _generate_caption_with_retry(product: str, category: str, price: float, image_path: str, description: str, max_retries: int = 2) -> str:
    """Generate caption with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            print(f"[MARKETING] Caption generation attempt {attempt + 1}/{max_retries}")
            caption = generate_ai_caption(product, category, price, image_path, description)
            if caption and caption.strip():
                print(f"[MARKETING] Caption generated successfully")
                return caption
        except Exception as e:
            if attempt < max_retries - 1:
                backoff_time = (2 ** attempt) + random.uniform(0, 0.5)
                print(f"[MARKETING] Caption generation failed: {e}. Retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
            else:
                print(f"[MARKETING] Caption generation failed after {max_retries} attempts: {e}")
                return "Elegant textile product for modern fashion."
    
    return "Elegant textile product for modern fashion."


def _batch_generate_posters_with_retry(image_paths: list, product_names: list, aspect_ratio: str = "", batch_size: int = 3, max_retries: int = 3) -> list:
    """Generate posters with robust retry logic and progress tracking."""
    global generation_progress
    
    print(f"[MARKETING] Starting robust batch poster generation")
    print(f"[MARKETING] Processing {len(image_paths)} images in batches of {batch_size}")
    
    all_results = []
    completed_items = 0
    
    # Process in batches
    for batch_idx in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[batch_idx:batch_idx + batch_size]
        batch_names = product_names[batch_idx:batch_idx + batch_size]
        
        batch_num = batch_idx // batch_size + 1
        total_batches = (len(image_paths) + batch_size - 1) // batch_size
        
        print(f"[MARKETING] Processing batch {batch_num}/{total_batches}")
        
        # Update progress for batch processing
        generation_progress["batch_progress"] = batch_num - 1
        update_progress("generating_posters", f"Processing batch {batch_num}/{total_batches}", completed_items, len(image_paths))
        
        # Retry logic for entire batch
        batch_success = False
        for attempt in range(max_retries):
            try:
                print(f"[MARKETING] Batch attempt {attempt + 1}/{max_retries}")
                
                # Generate posters for this batch
                batch_results = batch_generate_posters(
                    batch_paths, 
                    batch_names, 
                    aspect_ratio=aspect_ratio,
                    batch_size=len(batch_paths)  # Process all in this batch at once
                )
                
                # Check if we got results for all items in this batch
                if len(batch_results) == len(batch_paths):
                    print(f"[MARKETING] Batch {batch_num} completed successfully")
                    all_results.extend(batch_results)
                    completed_items += len(batch_paths)
                    batch_success = True
                    break
                else:
                    raise Exception(f"Expected {len(batch_paths)} results, got {len(batch_results)}")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    backoff_time = (2 ** attempt) + random.uniform(0, 2)
                    print(f"[MARKETING] Batch {batch_num} failed: {e}. Retrying in {backoff_time:.1f}s...")
                    update_progress("generating_posters", f"Batch {batch_num} failed, retrying...", completed_items, len(image_paths), f"Batch {batch_num} error: {str(e)}")
                    time.sleep(backoff_time)
                else:
                    print(f"[MARKETING] Batch {batch_num} failed after {max_retries} attempts: {e}")
                    update_progress("generating_posters", f"Batch {batch_num} failed", completed_items, len(image_paths), f"Batch {batch_num} failed: {str(e)}")
                    # Create failure results for this batch
                    for i, (path, name) in enumerate(zip(batch_paths, batch_names)):
                        all_results.append({
                            'success': False,
                            'error': f'Batch processing failed: {str(e)}',
                            'product_name': name,
                            'poster_path': None,
                            'prompt': None
                        })
                    completed_items += len(batch_paths)
    
    print(f"[MARKETING] Robust batch processing completed. Success: {sum(1 for r in all_results if r['success'])}/{len(all_results)}")
    return all_results


# GET: Download template file
@marketing_bp.route("/template", methods=["GET"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def download_template(current_user):
    """Generate and download CSV template for marketing content generation."""
    try:
        template_data = {
            'ProductName': ['Sample Saree', 'Designer Kurti', 'Silk Scarf'],
            'Category': ['Sarees', 'Kurtis', 'Accessories'],
            'Price': [2500, 1200, 800],
            'Description': ['Elegant wedding saree with intricate embroidery', 
                           'Stylish cotton kurti for casual wear',
                           'Premium silk scarf with traditional patterns'],
            'ImageURL': ['https://example.com/saree1.jpg', '', 'https://example.com/scarf1.jpg']  # Optional
        }
        
        df = pd.DataFrame(template_data)
        template_path = os.path.join(UPLOAD_FOLDER, 'marketing_template.csv')
        df.to_csv(template_path, index=False)
        
        return jsonify({
            "status": "success",
            "message": "Template generated successfully",
            "template_url": "/uploads/marketing/marketing_template.csv",
            "columns": {
                "ProductName": "Product name (required)",
                "Category": "Product category (required)", 
                "Price": "Product price (required)",
                "Description": "Product description (optional)",
                "ImageURL": "Image URL for enhanced content (optional)"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# POST: Upload CSV/Image → Generate AI Marketing Insights + Poster
@marketing_bp.route("/generate", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def generate_marketing_content(current_user):
    """
    Handles product uploads (CSV/XLSX/Image) and uses AI to generate:
    - Product captions (via Gemini)
    - Sales trends (if applicable)
    - AI-generated marketing poster (for image uploads)
    """
    try:
        # Reset progress before starting
        _reset_progress_internal()
        
        # Retrieve uploaded file
        file = request.files.get("file")
        if not file:
            return jsonify({
                "status": "error",
                "message": "No file provided"
            }), 400
        
        # Get generation options
        aspect_ratio = request.form.get("aspect_ratio", "")
        batch_size = int(request.form.get("batch_size", 3))
        
        # Get single image product details if provided
        product_name = request.form.get("product_name", "")
        product_category = request.form.get("product_category", "")
        product_price = request.form.get("product_price", "")
        product_description = request.form.get("product_description", "")
        
        print(f"[MARKETING] Generation options: aspect_ratio={aspect_ratio}, batch_size={batch_size}")
        if product_name:
            print(f"[MARKETING] Single image product: {product_name} ({product_category})")
        
        # Validate file upload
        is_valid, message = validate_file_upload(file, ['.csv', '.xlsx', '.png', '.jpg', '.jpeg'], max_size_mb=16)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        result = {"filename": filename}
        ai_captions = []
        trend_data = []

        # CASE 1: CSV / XLSX Upload
        if filename.endswith((".csv", ".xlsx")):
            print(f"[MARKETING] Processing CSV/XLSX upload: {filename}")
            df = pd.read_csv(filepath) if filename.endswith(".csv") else pd.read_excel(filepath)
            print(f"[MARKETING] Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")

            # Limit to first 5 rows for processing
            df = df.head(5)
            print(f"[MARKETING] Limited to first 5 rows for processing")

            # Required columns for marketing caption generation
            required_cols = {"ProductName", "Category", "Price"}
            if not required_cols.issubset(df.columns):
                print(f"[MARKETING ERROR] Missing required columns: {required_cols - set(df.columns)}")
                return jsonify({
                    "status": "error",
                    "message": f"Missing required columns: {', '.join(required_cols - set(df.columns))}"
                }), 400
            
            print(f"[MARKETING] Required columns present, processing data...")
            
            # Process with backend batch processing and retry logic
            try:
                ai_captions, trend_data = _process_csv_with_robust_batching(df, filename, aspect_ratio, batch_size)
                print(f"[MARKETING] CSV processing completed successfully. Captions: {len(ai_captions)}, Trends: {len(trend_data)}")
            except Exception as e:
                print(f"[MARKETING ERROR] CSV processing failed: {str(e)}")
                print(f"[MARKETING ERROR] Traceback: {traceback.format_exc()}")
                return jsonify({
                    "status": "error", 
                    "message": f"CSV processing failed: {str(e)}"
                }), 500
            
            # Optional: Forecast if Date/Sales columns exist
            if {"Date", "Sales"}.issubset(df.columns):
                print(f"[MARKETING] Date/Sales columns found, generating forecast...")
                if not trend_data:  # Only generate if not already done
                    trend_data = forecast_trends(df)
                result["forecast"] = trend_data
            else:
                print(f"[MARKETING] No Date/Sales columns found, skipping forecast")

            result.update({
                "type": "data",
                "ai_captions": ai_captions,
                "rows_processed": len(df),
                "analyst": current_user.get("username", "User")
            })
            
            print(f"[MARKETING] SUCCESS: CSV processing completed for {filename}")

        # CASE 2: Image Upload
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            print(f"[MARKETING] Processing image upload: {filename}")
            
            # Step 1: AI Caption from Image with product details if provided
            if product_name and product_category and product_price:
                caption = generate_ai_caption(
                    product_name,
                    product_category,
                    product_price,
                    image_path=filepath,
                    description=product_description
                )
                print(f"[MARKETING] Generated caption with product details: {caption}")
            else:
                caption = generate_ai_caption(
                    f"Uploaded product image: {filename}",
                    "Fabric/Clothing",
                    1200,
                    image_path=filepath
                )
                print(f"[MARKETING] Generated caption: {caption}")

            # Step 2: Generate AI Poster + Prompt with aspect ratio
            poster_prompt, poster_path = generate_marketing_poster(filepath, aspect_ratio=aspect_ratio)
            print(f"[MARKETING] Poster generation result: prompt={poster_prompt}, path={poster_path}")

            # Enhanced response structure
            result.update({
                "type": "image",
                "caption": caption,
                "poster_prompt": poster_prompt or "AI prompt not available.",
                "poster": f"/uploads/marketing/{os.path.basename(poster_path)}" if poster_path else None,
                "preview": f"/uploads/marketing/{filename}",
                "generation_method": _get_generation_method(poster_prompt, poster_path),
                "analyst": current_user.get("username", "User"),
                "product_details": {
                    "name": product_name,
                    "category": product_category,
                    "price": product_price,
                    "description": product_description
                } if product_name else None
            })
            
            if poster_path:
                print(f"[MARKETING] SUCCESS: Image processing completed for {filename}")
            else:
                print(f"[MARKETING] WARNING: Poster generation failed for {filename}")

        # SUCCESS RESPONSE - Save to history
        import json
        history_entry = MarketingHistory(
            user_id=current_user.get("id"),
            file_name=filename,
            file_type='csv' if filename.endswith(('.csv', '.xlsx')) else 'image',
            content_type=result.get("type", "unknown"),
            generated_content=json.dumps(result),
            status='completed',
            rows_processed=result.get("rows_processed", 0)
        )
        db.session.add(history_entry)
        db.session.commit()

        print(f"[Marketing AI] Processed file: {filename}")
        return jsonify({
            "status": "success",
            "message": "AI marketing content generated successfully!",
            "result": result,
            "history_id": history_entry.id
        }), 200

    except Exception as e:
        print("[Marketing AI Error]:", e)
        
        # Save failed attempt to history
        try:
            history_entry = MarketingHistory(
                user_id=current_user.get("id"),
                file_name=file.filename if 'file' in locals() else 'unknown',
                file_type='csv' if 'file' in locals() and file.filename.endswith(('.csv', '.xlsx')) else 'image',
                content_type='unknown',
                status='failed',
                error_message=str(e)
            )
            db.session.add(history_entry)
            db.session.commit()
        except:
            pass  # Don't fail the error response if history saving fails
        
        return jsonify({
            "status": "error",
            "message": "Failed to process marketing content.",
            "error": str(e)
        }), 500


# GET: Marketing History
@marketing_bp.route("/history", methods=["GET"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def get_marketing_history(current_user):
    """Get marketing content generation history for current user."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        history = MarketingHistory.query.filter_by(
            user_id=current_user.get("id")
        ).order_by(MarketingHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        import json
        history_data = []
        for item in history.items:
            try:
                content = json.loads(item.generated_content) if item.generated_content else {}
            except:
                content = {}
            
            history_data.append({
                "id": item.id,
                "file_name": item.file_name,
                "file_type": item.file_type,
                "content_type": item.content_type,
                "status": item.status,
                "rows_processed": item.rows_processed,
                "error_message": item.error_message,
                "created_at": item.created_at.isoformat(),
                "generated_content": content
            })
        
        return jsonify({
            "status": "success",
            "data": history_data,
            "pagination": {
                "page": history.page,
                "per_page": history.per_page,
                "total": history.total,
                "pages": history.pages,
                "has_next": history.has_next,
                "has_prev": history.has_prev
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE: Delete Marketing History Item
@marketing_bp.route("/history/<int:item_id>", methods=["DELETE"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def delete_marketing_history_item(current_user, item_id):
    """Delete a specific marketing history item."""
    try:
        # Find the history item
        history_item = MarketingHistory.query.filter_by(
            id=item_id,
            user_id=current_user.get("id")
        ).first()
        
        if not history_item:
            return jsonify({
                "status": "error",
                "message": "History item not found"
            }), 404
        
        # Delete the item
        db.session.delete(history_item)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "History item deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Allowed File Extensions
@marketing_bp.route("/allowed-extensions", methods=["GET"])
def get_allowed_extensions():
    """Return allowed file types for upload."""
    return jsonify({
        "status": "success",
        "allowed_extensions": sorted(list(ALLOWED_EXTENSIONS))
    }), 200
