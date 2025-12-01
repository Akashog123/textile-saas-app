import os
import pandas as pd
import requests
import time
import random
import traceback
import threading
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from utils.auth_utils import token_required, roles_required, check_shop_ownership
from utils.validation import validate_file_upload
from services.ai_service import generate_ai_caption, forecast_trends
from models.model import db, MarketingHistory, Product, ProductImage, Inventory

# Blueprint Setup
marketing_bp = Blueprint("marketing", __name__)

UPLOAD_FOLDER = "./uploads/marketing"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg"}

# Global progress tracking
progress_lock = threading.Lock()
generation_progress = {
    "status": "idle",
    "current_step": "",
    "current_item": 0,
    "total_items": 0,
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
            "errors": [],
            "start_time": None
        }

# Helper: File Validation
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _serialize_marketing_product(product: Product) -> dict:
    """Prepare inventory product payload for marketing UI."""
    primary_image = None
    try:
        primary_image = product.images.order_by(ProductImage.ordering.asc()).first()
    except Exception:
        primary_image = None

    inventory = getattr(product, "inventory", None)
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
        "price": float(product.price or 0),
        "description": product.description or "",
        "image_url": primary_image.url if primary_image else None,
        "stock": inventory.qty_available if inventory else 0,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    }


@marketing_bp.route("/inventory-products", methods=["GET"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def get_inventory_products_for_marketing(current_user):
    try:
        shop_id = request.args.get("shop_id", type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400

        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to access this shop"}), 403

        search = (request.args.get("search") or "").strip()
        limit = request.args.get("limit", default=12, type=int)
        limit = max(1, min(limit, 25))

        query = Product.query.filter_by(shop_id=shop_id)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(like),
                    Product.sku.ilike(like),
                    Product.category.ilike(like)
                )
            )

        products = query.order_by(Product.updated_at.desc()).limit(limit).all()
        return jsonify({
            "status": "success",
            "count": len(products),
            "data": [_serialize_marketing_product(product) for product in products]
        })
    except Exception as exc:
        print(f"[Marketing Inventory Error] {exc}")
        return jsonify({"status": "error", "message": "Failed to fetch inventory for marketing"}), 500


@marketing_bp.route("/generate/captions", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def generate_inventory_captions(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        shop_id = payload.get("shop_id")
        product_ids = payload.get("product_ids") or []

        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400

        if not isinstance(product_ids, list) or not product_ids:
            return jsonify({"status": "error", "message": "product_ids must contain at least one product"}), 400

        if len(product_ids) > 10:
            return jsonify({"status": "error", "message": "A maximum of 10 products can be selected at once"}), 400

        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to manage this shop"}), 403

        products = Product.query.filter(
            Product.shop_id == shop_id,
            Product.id.in_(product_ids)
        ).all()

        if not products:
            return jsonify({"status": "error", "message": "No valid products found for caption generation"}), 404

        product_map = {product.id: product for product in products}
        results = []

        for pid in product_ids:
            product = product_map.get(pid)
            if not product:
                continue

            caption = generate_ai_caption(
                product.name,
                product.category,
                float(product.price or 0),
                None,
                product.description
            )

            serialized = _serialize_marketing_product(product)
            share_text = (
                f"{product.name} | SKU: {product.sku or 'N/A'}\n"
                f"Price: ₹{float(product.price or 0):,.2f}\n"
                f"{caption}"
            )

            results.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
                "price": serialized["price"],
                "image_url": serialized["image_url"],
                "caption": caption,
                "share_text": share_text,
                "description": serialized["description"],
                "stock": serialized["stock"]
            })

        filename = f"inventory_marketing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        history_entry = MarketingHistory(
            user_id=current_user.get("id"),
            file_name=filename,
            file_type='inventory',
            content_type='caption',
            generated_content=json.dumps({"results": results}),
            status='completed',
            rows_processed=len(results)
        )
        db.session.add(history_entry)
        db.session.commit()

        return jsonify({
            "status": "success",
            "generated_at": datetime.utcnow().isoformat(),
            "results": results,
            "history_id": history_entry.id
        }), 200

    except Exception as exc:
        db.session.rollback()
        print(f"[Marketing Caption Error] {exc}")
        return jsonify({"status": "error", "message": "Failed to generate marketing captions"}), 500

# Helper: Download image from URL
def download_image_from_url(url: str, filename: str) -> str:
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

# GET: Get generation progress
@marketing_bp.route("/progress", methods=["GET"])
@token_required
def get_generation_progress(current_user):
    global generation_progress
    with progress_lock:
        elapsed_time = time.time() - generation_progress["start_time"] if generation_progress["start_time"] else None
        return jsonify({
            "status": generation_progress["status"],
            "current_step": generation_progress["current_step"],
            "current_item": generation_progress["current_item"],
            "total_items": generation_progress["total_items"],
            "progress_percentage": min(100, (generation_progress["current_item"] / max(1, generation_progress["total_items"])) * 100) if generation_progress["total_items"] > 0 else 0,
            "errors": generation_progress["errors"][-5:],
            "elapsed_time": elapsed_time
        })

# POST: Reset progress
@marketing_bp.route("/progress/reset", methods=["POST"])
@token_required
def reset_progress(current_user):
    _reset_progress_internal()
    return jsonify({"status": "success", "message": "Progress reset"})

# POST: Upload CSV/Image → Generate AI Marketing Captions
@marketing_bp.route("/generate", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'distributor', 'manufacturer')
def generate_marketing_content(current_user):
    try:
        _reset_progress_internal()
        
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        # Get single image product details if provided
        product_name = request.form.get("product_name", "")
        product_category = request.form.get("product_category", "")
        product_price = request.form.get("product_price", "")
        product_description = request.form.get("product_description", "")
        
        # Validate file upload
        is_valid, message = validate_file_upload(file, ['.csv', '.xlsx', '.png', '.jpg', '.jpeg'], max_size_mb=16)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        result = {"filename": filename}
        ai_captions = []
        trend_data = []

        # CASE 1: CSV / XLSX Upload
        if filename.endswith((".csv", ".xlsx")):
            df = pd.read_csv(filepath) if filename.endswith(".csv") else pd.read_excel(filepath)
            df = df.head(10) # Limit to 10 for quick processing (Story 5: < 1 min)
            
            required_cols = {"ProductName", "Category", "Price"}
            if not required_cols.issubset(df.columns):
                return jsonify({"status": "error", "message": f"Missing columns: {', '.join(required_cols - set(df.columns))}"}), 400
            
            update_progress("processing", "Starting CSV processing", 0, len(df))
            generation_progress["start_time"] = time.time()
            
            for idx, (_, row) in enumerate(df.iterrows()):
                product = row.get("ProductName", "Fabric")
                category = row.get("Category", "Textile")
                price = row.get("Price", 1000)
                description = row.get("Description", "")
                image_url = row.get("ImageURL", "")
                
                update_progress("processing", f"Generating caption for {product}", idx, len(df))
                
                # Download image if URL provided (for context)
                image_path = None
                if image_url and str(image_url).strip():
                    image_filename = f"product_{idx}_{secure_filename(filename.split('.')[0])}.jpg"
                    image_path = download_image_from_url(image_url, image_filename)

                caption = generate_ai_caption(product, category, price, image_path, description)
                
                ai_captions.append({
                    "product": product,
                    "category": category,
                    "price": price,
                    "description": description,
                    "image_url": image_url,
                    "caption": caption,
                    "has_image": bool(image_path),
                    "poster_path": f"/uploads/marketing/{os.path.basename(image_path)}" if image_path else None # Use original image
                })
            
            update_progress("completed", "Processing completed", len(df), len(df))
            
            result.update({
                "type": "data",
                "ai_captions": ai_captions,
                "rows_processed": len(df),
                "analyst": current_user.get("username", "User")
            })

        # CASE 2: Image Upload
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            update_progress("processing", "Generating caption for image", 0, 1)
            generation_progress["start_time"] = time.time()
            
            if product_name:
                caption = generate_ai_caption(product_name, product_category, product_price, filepath, product_description)
            else:
                caption = generate_ai_caption(f"Uploaded image: {filename}", "Fashion", 1000, filepath)
            
            update_progress("completed", "Processing completed", 1, 1)

            result.update({
                "type": "image",
                "caption": caption,
                "poster": f"/uploads/marketing/{filename}", # Use uploaded image
                "preview": f"/uploads/marketing/{filename}",
                "analyst": current_user.get("username", "User"),
                "product_details": {
                    "name": product_name,
                    "category": product_category,
                    "price": product_price,
                    "description": product_description
                } if product_name else None
            })

        # Save to history
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

        return jsonify({
            "status": "success",
            "message": "AI marketing content generated successfully!",
            "result": result,
            "history_id": history_entry.id
        }), 200

    except Exception as e:
        print("[Marketing AI Error]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# GET: Marketing History
@marketing_bp.route("/history", methods=["GET"])
@token_required
def get_marketing_history(current_user):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        history = MarketingHistory.query.filter_by(
            user_id=current_user.get("id")
        ).order_by(MarketingHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
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
                "created_at": item.created_at.isoformat(),
                "generated_content": content
            })
        
        return jsonify({
            "status": "success",
            "data": history_data,
            "pagination": {
                "page": history.page,
                "total": history.total,
                "pages": history.pages
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# DELETE: Delete History Item
@marketing_bp.route("/history/<int:item_id>", methods=["DELETE"])
@token_required
def delete_marketing_history_item(current_user, item_id):
    try:
        history_item = MarketingHistory.query.filter_by(id=item_id, user_id=current_user.get("id")).first()
        if not history_item:
            return jsonify({"status": "error", "message": "Item not found"}), 404
        
        db.session.delete(history_item)
        db.session.commit()
        return jsonify({"status": "success", "message": "Deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# GET: Template
@marketing_bp.route("/template", methods=["GET"])
@token_required
def download_template(current_user):
    try:
        template_data = {
            'ProductName': ['Sample Saree'],
            'Category': ['Sarees'],
            'Price': [2500],
            'Description': ['Elegant wedding saree'],
            'ImageURL': ['']
        }
        df = pd.DataFrame(template_data)
        template_path = os.path.join(UPLOAD_FOLDER, 'marketing_template.csv')
        df.to_csv(template_path, index=False)
        return jsonify({"status": "success", "template_url": "/uploads/marketing/marketing_template.csv"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
