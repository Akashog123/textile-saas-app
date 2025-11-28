from flask import Blueprint, jsonify, request, send_file
from models.model import db, Product, Inventory, SalesData, ProductCatalog, Shop
from utils.auth_utils import token_required, roles_required, check_shop_ownership
from utils.validation import validate_price, validate_quantity, validate_file_upload
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
from config import Config

inventory_bp = Blueprint("inventory", __name__)

# Fetch Inventory Items for a Shop
@inventory_bp.route("/", methods=["GET"])
@token_required
def get_inventory(current_user):
    """Fetch all inventory products for a given shop."""
    try:
        shop_id = request.args.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate shop ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to access this shop"}), 403

        products = Product.query.filter_by(shop_id=shop_id).order_by(Product.created_at.desc()).all()
        if products:
            data = []
            for p in products:
                inv = Inventory.query.filter_by(product_id=p.id).first()
                
                # Get the primary image for this product
                primary_image = p.images.filter_by(ordering=0).first()
                image_url = primary_image.url if primary_image else None
                
                # Convert to proper URL format if needed
                if image_url and not image_url.startswith('http'):
                    image_url = f"/uploads/{image_url}" if not image_url.startswith('/') else image_url
                
                data.append({
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "price": float(p.price),
                    "stock": inv.qty_available if inv else 0,
                    "minimum_stock": inv.safety_stock if inv else 0,
                    "sku": p.sku or f"AUTO-{p.id}",
                    "rating": round(p.rating, 1),
                    "shop_id": p.shop_id,
                    "image": image_url  # Only include real image, no placeholders
                })
            return jsonify({
                "status": "success",
                "message": "Inventory fetched successfully.",
                "data": data
            }), 200

        # fallback to Sales Data based generation
        sales = SalesData.query.filter_by(shop_id=shop_id).all()
        if not sales:
            return jsonify({"status": "success", "message": "No inventory data found.", "data": []}), 200

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
                    else f"{Config.PLACEHOLDER_IMAGE_SERVICE}/400x300?text=No+Image"
                ),
                "shop_id": shop_id
            })

        return jsonify({
            "status": "success",
            "message": "Inventory generated dynamically from sales data.",
            "data": dynamic_inventory
        }), 200

    except Exception as e:
        print(f"[Error - Get Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to fetch inventory.", "error": str(e)}), 500


# Import Inventory via CSV or Excel
@inventory_bp.route("/import", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def import_inventory(current_user):
    """Upload inventory via CSV/Excel for a shop."""
    try:
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
        df.columns = [c.lower() for c in df.columns]

        required_cols = {"name", "category", "price", "stock", "sku", "minimum_stock"}
        if not required_cols.issubset(set(df.columns)):
            return jsonify({"status": "error", "message": f"File must contain columns: {', '.join(required_cols)}"}), 400

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
        for _, row in df.iterrows():
            sku = str(row.get("sku", "")).strip()
            if not sku:
                # skip rows without SKU
                continue

            name = row.get("name", "Unnamed Product")
            category = row.get("category", "General")

            # make price and stock robust to bad values
            try:
                price = float(row.get("price", 0) or 0)
            except (ValueError, TypeError):
                price = 0.0
            try:
                stock = int(row.get("stock", 0) or 0)
            except (ValueError, TypeError):
                stock = 0
            try:
                minimum_stock = int(row.get("minimum_stock", 0) or 0)
            except (ValueError, TypeError):
                minimum_stock = 0

            # try to find existing product for this shop + sku
            product = Product.query.filter_by(sku=sku, shop_id=shop_id).first()
            if product:
                # update existing product
                product.name = name
                product.category = category
                product.price = price
                inv = Inventory.query.filter_by(product_id=product.id).first()
                if inv:
                    inv.qty_available = stock
                    inv.safety_stock = minimum_stock
                else:
                    db.session.add(Inventory(product_id=product.id, qty_available=stock, safety_stock=minimum_stock))
                updated += 1
            else:
                # create product with required shop_id
                new_product = Product(
                    name=name,
                    category=category,
                    price=price,
                    sku=sku,
                    shop_id=shop_id
                )
                db.session.add(new_product)
                try:
                    db.session.flush()  # to get new_product.id; may raise IntegrityError
                except Exception as e:
                    db.session.rollback()
                    # log and continue with next row
                    print(f"[Import - product create failed] sku={sku} error={e}")
                    continue

                db.session.add(Inventory(product_id=new_product.id, qty_available=stock, safety_stock=minimum_stock))
                added += 1

        db.session.commit()
        return jsonify({
            "status": "success",
            "message": f"Import successful. Added {added}, Updated {updated}.",
            "added": added,
            "updated": updated
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Import Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to import inventory.", "error": str(e)}), 500

# Edit Inventory (price, stock)
@inventory_bp.route("/edit", methods=["POST"])
@token_required
def edit_inventory(current_user):
    """Edit price or stock of a product."""
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        price = data.get("price")
        stock = data.get("stock")
        minimum_stock = data.get("minimum_stock")

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

        inv = Inventory.query.filter_by(product_id=product_id).first()
        if stock is not None:
            try:
                validated_stock = validate_quantity(stock)
                if inv:
                    inv.qty_available = validated_stock
                else:
                    db.session.add(Inventory(product_id=product.id, qty_available=validated_stock))
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        if minimum_stock is not None:
            try:
                validated_min_stock = validate_quantity(minimum_stock)
                if inv:
                    inv.safety_stock = validated_min_stock
                else:
                    db.session.add(Inventory(product_id=product.id, qty_available=0, safety_stock=validated_min_stock))
            except ValueError as e:
                return jsonify({"status": "error", "message": str(e)}), 400

        db.session.commit()
        return jsonify({"status": "success", "message": "Inventory updated successfully"}), 200

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
        return jsonify({"status": "success", "message": f"Deleted product ID {product_id} successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Delete Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to delete product.", "error": str(e)}), 500

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
            data.append({
                "Product Name": p.name,
                "Category": p.category or "General",
                "Price": float(p.price or 0),
                "Stock": inv.qty_available if inv else 0,
                "Minimum Stock": inv.safety_stock if inv else 0,
                "SKU": p.sku,
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
