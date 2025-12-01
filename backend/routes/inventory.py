from flask import Blueprint, jsonify, request, send_file
from models.model import db, Product, Inventory, SalesData, ProductCatalog, Shop
from utils.auth_utils import token_required, roles_required, check_shop_ownership
from utils.validation import validate_price, validate_quantity, validate_file_upload
from utils.inventory_utils import ensure_inventory_tracking_columns
from utils.response_helpers import (
    success_response, error_response, forbidden_response, 
    handle_exceptions
)
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
from config import Config

inventory_bp = Blueprint("inventory", __name__)

# Fetch Inventory Items for a Shop
@inventory_bp.route("/", methods=["GET"])
@token_required
@handle_exceptions("Get Inventory")
def get_inventory(current_user):
    """Fetch all inventory products for a given shop."""
    ensure_inventory_tracking_columns()
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
        df.columns = [c.lower() for c in df.columns]

        base_required = {"name", "category", "price", "sku", "minimum_stock"}
        quantity_column = "purchase_qty" if "purchase_qty" in df.columns else "stock"
        if quantity_column is None or quantity_column not in df.columns:
            return jsonify({
                "status": "error",
                "message": "File must include either 'purchase_qty' or 'stock' column to indicate amount purchased."
            }), 400

        required_cols = base_required | {quantity_column}
        if not required_cols.issubset(set(df.columns)):
            return jsonify({"status": "error", "message": f"File must contain columns: {', '.join(sorted(required_cols))}"}), 400

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
                purchase_qty_raw = row.get(quantity_column, 0)
                purchase_qty = int(purchase_qty_raw if purchase_qty_raw is not None else 0)
            except (ValueError, TypeError):
                purchase_qty = 0
            if purchase_qty < 0:
                purchase_qty = 0
            try:
                minimum_stock = int(row.get("minimum_stock", 0) or 0)
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
        return jsonify({
            "status": "success",
            "message": f"Import successful. Added {added}, Updated {updated}.",
            "added": added,
            "updated": updated,
            "total_units_added": total_units_added,
            "restock_summary": restock_summary
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Import Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to import inventory.", "error": str(e)}), 500

# Edit Inventory (price, stock)
@inventory_bp.route("/edit", methods=["POST"])
@token_required
def edit_inventory(current_user):
    """Edit price, stock, or distributor of a product."""
    try:
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
