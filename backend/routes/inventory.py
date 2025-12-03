from flask import Blueprint, jsonify, request, send_file, Response, current_app
from models.model import db, Product, Inventory, SalesData, ProductCatalog, Shop, ProductImage
from utils.auth_utils import token_required, roles_required, check_shop_ownership
from utils.validation import validate_price, validate_quantity, validate_file_upload
from utils.inventory_utils import ensure_inventory_tracking_columns, ensure_product_image_url_column
from utils.export_data import schedule_rag_refresh
from utils.csv_templates import (
    get_template_csv, validate_columns, TEMPLATE_INFO
)
from utils.response_helpers import (
    success_response, error_response, forbidden_response, 
    handle_exceptions
)
import os
import pandas as pd
from io import BytesIO
from datetime import datetime
from config import Config

inventory_bp = Blueprint("inventory", __name__)


# ============================================================================
# CSV TEMPLATE DOWNLOADS
# ============================================================================

@inventory_bp.route("/template/<template_type>", methods=["GET"])
def download_template(template_type):
    """
    Download CSV template for imports.
    
    Args:
        template_type: 'inventory', 'sales', or 'marketing'
        
    Query params:
        include_sample: 'true' (default) or 'false' - whether to include sample row
    """
    valid_types = ["inventory", "sales", "marketing"]
    if template_type not in valid_types:
        return jsonify({
            "status": "error",
            "message": f"Invalid template type. Available: {', '.join(valid_types)}"
        }), 400
    
    include_sample = request.args.get("include_sample", "true").lower() == "true"
    
    try:
        csv_content = get_template_csv(template_type, include_sample=include_sample)
        
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={template_type}_template.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@inventory_bp.route("/template/<template_type>/info", methods=["GET"])
def get_template_info(template_type):
    """Get template column information and requirements."""
    if template_type not in TEMPLATE_INFO:
        return jsonify({
            "status": "error",
            "message": f"Unknown template type. Available: {', '.join(TEMPLATE_INFO.keys())}"
        }), 400
    
    return jsonify({
        "status": "success",
        "template": TEMPLATE_INFO[template_type]
    })


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

# Fetch Inventory Items for a Shop
@inventory_bp.route("/", methods=["GET"])
@token_required
@handle_exceptions("Get Inventory")
def get_inventory(current_user):
    """Fetch all inventory products for a given shop."""
    ensure_inventory_tracking_columns()
    ensure_product_image_url_column()
    shop_id = request.args.get("shop_id")
    if not shop_id:
        return error_response("shop_id is required", 400)
    
    # Validate shop ownership
    if not check_shop_ownership(current_user.get("id"), shop_id):
        return forbidden_response("You don't have permission to access this shop")

    products = Product.query.filter_by(shop_id=shop_id).order_by(Product.created_at.desc()).all()
    if products:
        # Use model's to_inventory_dict method for consistent serialization
        data = [p.to_inventory_dict() for p in products]
        return success_response(
            data=data,
            message="Inventory fetched successfully."
        )

    # fallback to Sales Data based generation
    sales = SalesData.query.filter_by(shop_id=shop_id).all()
    if not sales:
        return success_response(data=[], message="No inventory data found.")

    df = pd.DataFrame([{
        "product_id": s.product_id,
        "quantity_sold": s.quantity_sold,
        "revenue": s.revenue
    } for s in sales])

    grouped = df.groupby("product_id").agg({"quantity_sold": "sum", "revenue": "sum"}).reset_index()
    product_map = {
        str(p.product_id): {
            "name": p.product_name,
            "category": p.category,
            "image_url": p.image_url
        }
        for p in ProductCatalog.query.filter(
            ProductCatalog.product_id.in_(grouped["product_id"].tolist())
        ).all()
    }

    dynamic_inventory = []
    for _, row in grouped.iterrows():
        pinfo = product_map.get(str(row["product_id"]), {})
        dynamic_inventory.append({
            "id": row["product_id"],
            "name": pinfo.get("name", "Unknown Product"),
            "category": pinfo.get("category", "N/A"),
            "price": round(row["revenue"] / max(row["quantity_sold"], 1), 2),
            "stock": max(1000 - row["quantity_sold"], 0),
            "sku": f"AUTO-{row['product_id']}",
            "rating": 4.2,
            "image": (
                f"{Config.API_BASE_URL}{pinfo.get('image_url', '')}"
                if pinfo.get("image_url")
                else None
            ),
            "shop_id": shop_id
        })

    return success_response(
        data=dynamic_inventory,
        message="Inventory generated dynamically from sales data."
    )


# Import Inventory via CSV or Excel
@inventory_bp.route("/import", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def import_inventory(current_user):
    """Upload inventory via CSV/Excel for a shop."""
    try:
        ensure_inventory_tracking_columns()
        file = request.files.get("file")
        shop_id_raw = request.form.get("shop_id")

        if not file or not shop_id_raw:
            return jsonify({"status": "error", "message": "Missing file or shop_id"}), 400
        
        # Validate shop ownership
        if not check_shop_ownership(current_user.get("id"), shop_id_raw):
            return jsonify({"status": "error", "message": "You don't have permission to manage this shop"}), 403
        
        # Validate file upload
        is_valid, message = validate_file_upload(file, ['.csv', '.xlsx', '.xls'], max_size_mb=16)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        filename = file.filename.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "File must be .csv or .xlsx"}), 400

        # Normalize columns to lowercase
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Support common column aliases
        column_aliases = {
            'stock': 'purchase_qty',
            'quantity': 'purchase_qty',
            'qty': 'purchase_qty',
            'initial_stock': 'purchase_qty',
            'product_name': 'name',
            'product': 'name',
            'min_stock': 'minimum_stock',
            'safety_stock': 'minimum_stock',
            'reorder_level': 'minimum_stock',
            'unit_price': 'price',
            'cost': 'price',
        }
        df.columns = [column_aliases.get(c, c) for c in df.columns]

        # Validate columns using centralized template
        is_valid, missing, message = validate_columns(df.columns.tolist(), "inventory")
        if not is_valid:
            return jsonify({
                "status": "error", 
                "message": message,
                "hint": "Download the template from GET /api/v1/inventory/template/inventory"
            }), 400

        # ensure shop_id is an integer (used in queries and new products)
        try:
            shop_id = int(shop_id_raw)
        except (ValueError, TypeError):
            return jsonify({"status":"error","message":"invalid shop_id"}), 400

        # try to determine default shop owner (if exists)
        shop_obj = Shop.query.get(shop_id)
        if not shop_obj:
            return jsonify({"status":"error","message":"Shop not found"}), 404

        added, updated = 0, 0
        total_units_added = 0
        restock_summary = []
        for _, row in df.iterrows():
            sku = str(row.get("sku", "")).strip()
            if not sku or pd.isna(row.get("sku")):
                # skip rows without SKU
                continue

            name_val = row.get("name", "Unnamed Product")
            name = str(name_val) if not pd.isna(name_val) else "Unnamed Product"
            
            category_val = row.get("category", "General")
            category = str(category_val) if not pd.isna(category_val) else "General"

            # make price and stock robust to bad values
            try:
                price_val = row.get("price", 0)
                if pd.isna(price_val):
                    price_val = 0
                price = float(price_val or 0)
            except (ValueError, TypeError):
                price = 0.0
            try:
                purchase_qty_raw = row.get("purchase_qty", 0)
                if pd.isna(purchase_qty_raw):
                    purchase_qty_raw = 0
                purchase_qty = int(float(purchase_qty_raw or 0))  # float first to handle "50.0" strings
            except (ValueError, TypeError):
                purchase_qty = 0
            if purchase_qty < 0:
                purchase_qty = 0
            try:
                min_stock_val = row.get("minimum_stock", 0)
                if pd.isna(min_stock_val):
                    min_stock_val = 0
                minimum_stock = int(float(min_stock_val or 0))
            except (ValueError, TypeError):
                minimum_stock = 0

            # try to find existing product for this shop + sku
            product = Product.query.filter_by(sku=sku, shop_id=shop_id).first()
            
            # Get distributor_id from row if provided
            distributor_id = None
            if "distributor_id" in df.columns:
                try:
                    dist_id = row.get("distributor_id")
                    if dist_id and not pd.isna(dist_id):
                        distributor_id = int(dist_id)
                except (ValueError, TypeError):
                    distributor_id = None
            
            if product:
                # update existing product
                product.name = name
                product.category = category
                product.price = price
                if distributor_id:
                    product.distributor_id = distributor_id
                
                inv = Inventory.query.filter_by(product_id=product.id).first()
                if inv:
                    if purchase_qty:
                        inv.qty_available = max(0, (inv.qty_available or 0) + purchase_qty)
                        inv.total_purchased = (inv.total_purchased or 0) + purchase_qty
                        total_units_added += purchase_qty
                    inv.safety_stock = minimum_stock
                else:
                    inv = Inventory(
                        product_id=product.id,
                        qty_available=purchase_qty,
                        safety_stock=minimum_stock,
                        total_purchased=purchase_qty,
                        total_sold=0
                    )
                    db.session.add(inv)
                    total_units_added += purchase_qty
                updated += 1
            else:
                # create product with required shop_id
                new_product = Product(
                    name=name,
                    category=category,
                    price=price,
                    sku=sku,
                    shop_id=shop_id,
                    distributor_id=distributor_id
                )
                db.session.add(new_product)
                try:
                    db.session.flush()  # to get new_product.id; may raise IntegrityError
                except Exception as e:
                    db.session.rollback()
                    # log and continue with next row
                    print(f"[Import - product create failed] sku={sku} error={e}")
                    continue


                db.session.add(Inventory(
                    product_id=new_product.id,
                    qty_available=purchase_qty,
                    safety_stock=minimum_stock,
                    total_purchased=purchase_qty,
                    total_sold=0
                ))
                added += 1
                total_units_added += purchase_qty

            restock_summary.append({
                "sku": sku,
                "product_name": name,
                "added_quantity": purchase_qty,
                "minimum_stock": minimum_stock,
                "operation": "updated" if product else "added"
            })

        db.session.commit()
        
        # Trigger RAG refresh if new products were added
        if added > 0:
            schedule_rag_refresh(current_app._get_current_object(), delay_seconds=3)
        
        return jsonify({
            "status": "success",
            "message": f"Import successful. Added {added}, Updated {updated}. Use ZIP bulk upload for images.",
            "added": added,
            "updated": updated,
            "total_units_added": total_units_added,
            "restock_summary": restock_summary,
            "image_upload_hint": "Upload product images via POST /api/v1/inventory/images/bulk-upload with a ZIP file containing SKU-named images (e.g., COT-001.jpg, COT-001_1.jpg)"
        }), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"[Error - Import Inventory] {e}\n{error_trace}")
        return jsonify({"status": "error", "message": "Failed to import inventory.", "error": str(e)}), 500

# Edit Inventory (price, stock)
@inventory_bp.route("/edit", methods=["POST"])
@token_required
def edit_inventory(current_user):
    """Edit price, stock, distributor, or images of a product."""
    try:
        # Support both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            # Convert string values to appropriate types
            if 'price' in data and data['price']:
                data['price'] = float(data['price'])
            if 'stock' in data and data['stock']:
                data['stock'] = int(data['stock'])
            if 'minimum_stock' in data and data['minimum_stock']:
                data['minimum_stock'] = int(data['minimum_stock'])
            if 'distributor_id' in data:
                if data['distributor_id'] == '' or data['distributor_id'] == 'null':
                    data['distributor_id'] = None
                else:
                    data['distributor_id'] = int(data['distributor_id'])
        else:
            data = request.get_json()
        
        product_id = data.get("product_id")
        price = data.get("price")
        stock = data.get("stock")
        minimum_stock = data.get("minimum_stock")
        distributor_id = data.get("distributor_id")  # Can be set, updated, or cleared (null)

        if not product_id:
            return jsonify({"status": "error", "message": "product_id required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), product.shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to edit this product"}), 403

        if price is not None:
            try:
                validated_price = validate_price(price)
                product.price = validated_price
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        # Handle distributor assignment
        # distributor_id can be: integer (assign), null/None (clear), or not provided (no change)
        if "distributor_id" in data:
            if distributor_id is None:
                # Clear distributor assignment
                product.distributor_id = None
            else:
                # Validate distributor exists and has distributor role
                from models.model import User
                distributor = User.query.filter_by(id=distributor_id, role="distributor").first()
                if not distributor:
                    return jsonify({
                        "status": "error", 
                        "message": "Invalid distributor_id. Must be a registered distributor."
                    }), 400
                product.distributor_id = distributor_id

        inv = Inventory.query.filter_by(product_id=product_id).first()
        
        # Consolidate inventory creation - create once if needed
        if not inv and (stock is not None or minimum_stock is not None):
            inv = Inventory(product_id=product.id, qty_available=0, safety_stock=0)
            db.session.add(inv)
        
        if stock is not None:
            try:
                validated_stock = validate_quantity(stock)
                inv.qty_available = validated_stock
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        if minimum_stock is not None:
            try:
                validated_min_stock = validate_quantity(minimum_stock)
                inv.safety_stock = validated_min_stock
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400

        # Handle image uploads (multipart form data)
        images_uploaded = 0
        if request.files:
            import os
            import uuid
            from werkzeug.utils import secure_filename
            from config import Config
            
            # Create product images folder
            product_images_folder = os.path.join(Config.UPLOAD_FOLDER, "product_images")
            os.makedirs(product_images_folder, exist_ok=True)
            
            allowed_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            
            # Get uploaded files (support 'images' or 'images[]')
            files = request.files.getlist("images") or request.files.getlist("images[]")
            
            if files:
                # Get current image count
                existing_count = ProductImage.query.filter_by(product_id=product_id).count()
                max_images = 4
                
                for idx, file in enumerate(files):
                    if existing_count + idx >= max_images:
                        break  # Max 4 images
                    
                    if not file or file.filename == '':
                        continue
                    
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext not in allowed_exts:
                        continue
                    
                    # Validate file
                    is_valid, message = validate_file_upload(file, allowed_exts, max_size_mb=5)
                    if not is_valid:
                        continue
                    
                    # Generate unique filename
                    unique_id = uuid.uuid4().hex[:8]
                    safe_name = secure_filename(file.filename)
                    filename = f"product_{product_id}_{unique_id}_{safe_name}"
                    filepath = os.path.join(product_images_folder, filename)
                    
                    # Save file
                    file.seek(0)
                    file.save(filepath)
                    
                    # Get next ordering value
                    max_order = db.session.query(db.func.max(ProductImage.ordering)).filter_by(product_id=product_id).scalar() or -1
                    
                    # Create database record
                    product_image = ProductImage(
                        product_id=product_id,
                        url=f"/uploads/product_images/{filename}",
                        alt=f"{product.name} image {max_order + 2}",
                        ordering=max_order + 1
                    )
                    db.session.add(product_image)
                    images_uploaded += 1
                    
                    # Set first uploaded image as primary if product has no image_url
                    if not product.image_url:
                        product.image_url = f"/uploads/product_images/{filename}"

        db.session.commit()
        
        message = "Inventory updated successfully"
        if images_uploaded > 0:
            message = f"Inventory updated and {images_uploaded} image(s) uploaded"
        
        return jsonify({"status": "success", "message": message, "images_uploaded": images_uploaded}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Edit Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to update inventory.", "error": str(e)}), 500

# Delete Product
@inventory_bp.route("/delete", methods=["DELETE"])
@token_required
def delete_inventory(current_user):
    """Delete a product and its inventory entry."""
    try:
        product_id = request.args.get("product_id")
        if not product_id:
            return jsonify({"status": "error", "message": "product_id required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), product.shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to delete this product"}), 403

        Inventory.query.filter_by(product_id=product_id).delete()
        db.session.delete(product)
        db.session.commit()

        schedule_rag_refresh(current_app._get_current_object(), delay_seconds=2)
        
        return jsonify({"status": "success", "message": f"Deleted product ID {product_id} successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Delete Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to delete product.", "error": str(e)}), 500


# ============================================================================
# PRODUCT IMAGE MANAGEMENT ENDPOINTS
# ============================================================================

@inventory_bp.route("/product/<int:product_id>/images", methods=["GET"])
@token_required
def get_product_images(current_user, product_id):
    """Get all images for a product."""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        images = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.ordering).all()
        
        return jsonify({
            "status": "success",
            "product_id": product_id,
            "images": [
                {
                    "id": img.id,
                    "url": img.url,
                    "alt": img.alt,
                    "ordering": img.ordering
                }
                for img in images
            ],
            "max_images": 4,
            "can_upload_more": len(images) < 4
        }), 200
    except Exception as e:
        print(f"[Error - Get Product Images] {e}")
        return jsonify({"status": "error", "message": "Failed to fetch images"}), 500


@inventory_bp.route("/product/<int:product_id>/images/<int:image_id>", methods=["DELETE"])
@token_required
def delete_product_image(current_user, product_id, image_id):
    """Delete a specific product image."""
    import os
    from config import Config
    
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), product.shop_id):
            return jsonify({"status": "error", "message": "Not authorized"}), 403
        
        image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
        if not image:
            return jsonify({"status": "error", "message": "Image not found"}), 404
        
        # Delete physical file
        if image.url.startswith("/uploads/"):
            filepath = os.path.join(Config.BASE_DIR, image.url.lstrip("/"))
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"[Warning] Could not delete file: {e}")
        
        # If this was the primary image, update product.image_url
        if product.image_url == image.url:
            # Get next image if exists
            next_image = ProductImage.query.filter(
                ProductImage.product_id == product_id,
                ProductImage.id != image_id
            ).order_by(ProductImage.ordering).first()
            product.image_url = next_image.url if next_image else None
        
        db.session.delete(image)
        
        # Re-order remaining images
        remaining = ProductImage.query.filter_by(product_id=product_id).filter(ProductImage.id != image_id).order_by(ProductImage.ordering).all()
        for idx, img in enumerate(remaining):
            img.ordering = idx
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Image deleted",
            "remaining_images": len(remaining)
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[Error - Delete Product Image] {e}")
        return jsonify({"status": "error", "message": "Failed to delete image"}), 500


@inventory_bp.route("/product/<int:product_id>/images/<int:image_id>/set-primary", methods=["PUT"])
@token_required
def set_primary_product_image(current_user, product_id, image_id):
    """Set a product image as the primary image."""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), product.shop_id):
            return jsonify({"status": "error", "message": "Not authorized"}), 403
        
        image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
        if not image:
            return jsonify({"status": "error", "message": "Image not found"}), 404
        
        # Update product's primary image
        product.image_url = image.url
        
        # Reorder to put this image first
        all_images = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.ordering).all()
        for img in all_images:
            if img.id == image_id:
                img.ordering = 0
            elif img.ordering < image.ordering:
                img.ordering += 1
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Primary image updated",
            "primary_image_url": image.url
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[Error - Set Primary Image] {e}")
        return jsonify({"status": "error", "message": "Failed to set primary image"}), 500

# Export Inventory as Excel
@inventory_bp.route("/export", methods=["GET"])
@token_required
def export_inventory(current_user):
    """Download all inventory for a shop as Excel."""
    try:
        shop_id = request.args.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to export this shop's inventory"}), 403

        products = Product.query.filter_by(shop_id=shop_id).all()
        if not products:
            return jsonify({"status": "error", "message": "No products found to export"}), 404

        data = []
        for p in products:
            inv = Inventory.query.filter_by(product_id=p.id).first()
            distributor_name = p.distributor.full_name if p.distributor else ""
            data.append({
                "Product Name": p.name,
                "Category": p.category or "General",
                "Price": float(p.price or 0),
                "Stock": inv.qty_available if inv else 0,
                "Minimum Stock": inv.safety_stock if inv else 0,
                "SKU": p.sku,
                "Distributor ID": p.distributor_id or "",
                "Distributor Name": distributor_name,
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        filename = f"inventory_export_{shop_id}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print(f"[Error - Export Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to export inventory.", "error": str(e)}), 500


# Bulk assign distributor to products
@inventory_bp.route("/assign-distributor", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def bulk_assign_distributor(current_user):
    """
    Bulk assign or clear distributor for multiple products.
    Useful for grouping products by supplier for efficient reordering.
    
    Body:
    {
        "shop_id": 1,
        "product_ids": [1, 2, 3],
        "distributor_id": 5  // or null to clear
    }
    """
    try:
        data = request.get_json() or {}
        shop_id = data.get("shop_id")
        product_ids = data.get("product_ids", [])
        distributor_id = data.get("distributor_id")  # Can be int or null
        
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        if not product_ids or not isinstance(product_ids, list):
            return jsonify({"status": "error", "message": "product_ids must be a non-empty list"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to manage this shop"}), 403
        
        # Validate distributor if provided
        distributor = None
        if distributor_id is not None:
            from models.model import User
            distributor = User.query.filter_by(id=distributor_id, role="distributor").first()
            if not distributor:
                return jsonify({
                    "status": "error",
                    "message": "Invalid distributor_id. Must be a registered distributor."
                }), 400
        
        # Get products belonging to this shop
        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.shop_id == shop_id
        ).all()
        
        if not products:
            return jsonify({"status": "error", "message": "No valid products found for this shop"}), 404
        
        updated_count = 0
        updated_products = []
        
        for product in products:
            product.distributor_id = distributor_id
            updated_count += 1
            updated_products.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "distributor_id": distributor_id,
                "distributor_name": distributor.full_name if distributor else None
            })
        
        db.session.commit()
        
        action = "assigned" if distributor_id else "cleared"
        return jsonify({
            "status": "success",
            "message": f"Distributor {action} for {updated_count} product(s)",
            "updated_count": updated_count,
            "updated_products": updated_products,
            "distributor": {
                "id": distributor.id,
                "name": distributor.full_name,
                "contact": distributor.contact,
                "email": distributor.email
            } if distributor else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[Error - Bulk Assign Distributor] {e}")
        return jsonify({"status": "error", "message": "Failed to assign distributor", "error": str(e)}), 500


# Get available distributors for assignment
@inventory_bp.route("/distributors", methods=["GET"])
@token_required
def get_available_distributors(current_user):
    """
    Get list of registered distributors for product assignment.
    Shop owners can use this to find distributors to assign to their products.
    """
    try:
        from models.model import User
        
        search = request.args.get("search", "").strip()
        
        query = User.query.filter_by(role="distributor", approved=True)
        
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.city.ilike(f"%{search}%")
                )
            )
        
        distributors = query.order_by(User.full_name).limit(50).all()
        
        result = [{
            "id": d.id,
            "full_name": d.full_name,
            "username": d.username,
            "email": d.email,
            "contact": d.contact,
            "city": d.city,
            "state": d.state
        } for d in distributors]
        
        return jsonify({
            "status": "success",
            "count": len(result),
            "distributors": result
        }), 200
        
    except Exception as e:
        print(f"[Error - Get Distributors] {e}")
        return jsonify({"status": "error", "message": "Failed to fetch distributors"}), 500


# Bulk Upload Product Images via ZIP
@inventory_bp.route("/images/bulk-upload", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def bulk_upload_product_images(current_user):
    """
    Upload product images in bulk via ZIP file.
    
    Images should be named by SKU:
    - Single image: SKU.jpg (e.g., COT-001.jpg)
    - Multiple images: SKU_1.jpg, SKU_2.jpg (e.g., COT-001_1.jpg, COT-001_2.jpg)
    
    Supported formats: .jpg, .jpeg, .png, .webp
    Max 4 images per product.
    """
    import zipfile
    import tempfile
    import shutil
    import uuid
    from werkzeug.utils import secure_filename
    
    try:
        shop_id = request.form.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to manage this shop"}), 403
        
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No ZIP file provided"}), 400
        
        if not file.filename.lower().endswith('.zip'):
            return jsonify({"status": "error", "message": "File must be a .zip archive"}), 400
        
        # Validate file size (50MB max for ZIP)
        is_valid, message = validate_file_upload(file, ['.zip'], max_size_mb=50)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400
        
        # Create temp directory for extraction
        temp_dir = tempfile.mkdtemp()
        allowed_exts = {'.jpg', '.jpeg', '.png', '.webp'}
        
        try:
            # Extract ZIP
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Create product images folder
            product_images_folder = os.path.join(Config.UPLOAD_FOLDER, "product_images")
            os.makedirs(product_images_folder, exist_ok=True)
            
            # Get all products for this shop
            products = Product.query.filter_by(shop_id=shop_id).all()
            sku_to_product = {p.sku.upper(): p for p in products if p.sku}
            
            results = {
                "matched": 0,
                "images_added": 0,
                "skipped": [],
                "errors": []
            }
            
            # Process images by SKU
            sku_images = {}  # {SKU: [(ordering, filepath), ...]}
            
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in allowed_exts:
                        continue
                    
                    # Parse SKU from filename
                    base_name = os.path.splitext(filename)[0]
                    
                    # Handle SKU_1, SKU_2 pattern or just SKU
                    if '_' in base_name and base_name.rsplit('_', 1)[1].isdigit():
                        sku = base_name.rsplit('_', 1)[0].upper()
                        ordering = int(base_name.rsplit('_', 1)[1]) - 1  # 0-indexed
                    else:
                        sku = base_name.upper()
                        ordering = 0
                    
                    filepath = os.path.join(root, filename)
                    
                    if sku not in sku_images:
                        sku_images[sku] = []
                    sku_images[sku].append((ordering, filepath, filename))
            
            # Process each SKU's images
            for sku, images in sku_images.items():
                if sku not in sku_to_product:
                    results["skipped"].append(f"{sku} - Product not found")
                    continue
                
                product = sku_to_product[sku]
                
                # Sort by ordering and limit to 4
                images.sort(key=lambda x: x[0])
                images = images[:4]
                
                # Delete existing images for this product
                ProductImage.query.filter_by(product_id=product.id).delete()
                
                # Reset product's primary image_url
                product.image_url = None
                
                for idx, (_, src_path, orig_filename) in enumerate(images):
                    # Generate unique filename
                    unique_id = uuid.uuid4().hex[:8]
                    ext = os.path.splitext(orig_filename)[1].lower()
                    new_filename = f"product_{product.id}_{unique_id}{ext}"
                    dest_path = os.path.join(product_images_folder, new_filename)
                    
                    # Copy file
                    shutil.copy2(src_path, dest_path)
                    
                    # Create database record
                    image_url = f"/uploads/product_images/{new_filename}"
                    product_image = ProductImage(
                        product_id=product.id,
                        url=image_url,
                        alt=f"{product.name} image {idx + 1}",
                        ordering=idx
                    )
                    db.session.add(product_image)
                    results["images_added"] += 1
                    
                    # Set first image (ordering=0) as product's primary image_url
                    if idx == 0:
                        product.image_url = image_url
                
                results["matched"] += 1
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Bulk upload complete. {results['matched']} products updated with {results['images_added']} images.",
                **results
            }), 200
            
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except zipfile.BadZipFile:
        return jsonify({"status": "error", "message": "Invalid or corrupted ZIP file"}), 400
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[Error - Bulk Upload Images] {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Failed to process images", "error": str(e)}), 500
