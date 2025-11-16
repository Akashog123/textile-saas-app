from flask import Blueprint, jsonify, request, send_file
from models.model import db, Product, Inventory, SalesData, ProductCatalog,Shop
import pandas as pd
from io import BytesIO
from datetime import datetime

inventory_bp = Blueprint("inventory", __name__)

# Fetch Inventory Items for a Shop
@inventory_bp.route("/", methods=["GET"])
def get_inventory():
    """Fetch all inventory products for a given shop."""
    try:
        shop_id = request.args.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400

        products = Product.query.filter_by(shop_id=shop_id).order_by(Product.created_at.desc()).all()
        if products:
            data = []
            for p in products:
                inv = Inventory.query.filter_by(product_id=p.id).first()
                data.append({
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "price": float(p.price),
                    "stock": inv.qty_available,
                    "sku": p.sku or f"AUTO-{p.id}",
                    "rating": round(p.rating, 1),
                    "shop_id": p.shop_id
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
                    f"http://127.0.0.1:5001{pinfo.get('image_url', '')}"
                    if pinfo.get("image_url")
                    else "https://placehold.co/400x300?text=No+Image"
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
def import_inventory():
    """Upload inventory via CSV/Excel for a shop."""
    try:
        file = request.files.get("file")
        shop_id_raw = request.form.get("shop_id")

        if not file or not shop_id_raw:
            return jsonify({"status": "error", "message": "Missing file or shop_id"}), 400

        filename = file.filename.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "File must be .csv or .xlsx"}), 400

        # Normalize columns to lowercase
        df.columns = [c.lower() for c in df.columns]

        required_cols = {"name", "category", "price", "stock", "sku"}
        if not required_cols.issubset(set(df.columns)):
            return jsonify({"status": "error", "message": f"File must contain columns: {', '.join(required_cols)}"}), 400

        # ensure shop_id is an integer (used in queries and new products)
        try:
            shop_id = int(shop_id_raw)
        except (ValueError, TypeError):
            return jsonify({"status":"error","message":"invalid shop_id"}), 400

        # try to determine default seller_id from the shop owner (if exists)
        shop_obj = Shop.query.get(shop_id)
        default_seller_id = shop_obj.owner_id if shop_obj and shop_obj.owner_id else 1

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

            # resolve seller_id: CSV column -> form param -> shop owner -> fallback 1
            seller_id = None
            if "seller_id" in df.columns:
                raw = row.get("seller_id")
                if pd.notna(raw) and raw != "":
                    try:
                        seller_id = int(raw)
                    except (ValueError, TypeError):
                        seller_id = None

            if not seller_id:
                form_seller = request.form.get("seller_id")
                if form_seller:
                    try:
                        seller_id = int(form_seller)
                    except (ValueError, TypeError):
                        seller_id = None

            if not seller_id:
                seller_id = default_seller_id

            # try to find existing product for this shop + sku
            product = Product.query.filter_by(sku=sku, shop_id=shop_id).first()
            if product:
                # update existing product
                product.name = name
                product.category = category
                product.price = price
                # ensure seller_id is set (update it if missing/different)
                product.seller_id = seller_id
                inv = Inventory.query.filter_by(product_id=product.id).first()
                if inv:
                    inv.qty_available = stock
                else:
                    db.session.add(Inventory(product_id=product.id, qty_available=stock))
                updated += 1
            else:
                # create product with required seller_id and shop_id
                new_product = Product(
                    name=name,
                    category=category,
                    price=price,
                    sku=sku,
                    shop_id=shop_id,
                    seller_id=seller_id
                )
                db.session.add(new_product)
                try:
                    db.session.flush()  # to get new_product.id; may raise IntegrityError
                except Exception as e:
                    db.session.rollback()
                    # log and continue with next row
                    print(f"[Import - product create failed] sku={sku} error={e}")
                    continue

                db.session.add(Inventory(product_id=new_product.id, qty_available=stock))
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
def edit_inventory():
    """Edit price or stock of a product."""
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        price = data.get("price")
        stock = data.get("stock")

        if not product_id:
            return jsonify({"status": "error", "message": "product_id required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404

        if price is not None:
            product.price = float(price)

        inv = Inventory.query.filter_by(product_id=product_id).first()
        if inv:
            inv.qty_available = int(stock or inv.qty_available)
        elif stock is not None:
            db.session.add(Inventory(product_id=product.id, qty_available=int(stock)))

        db.session.commit()
        return jsonify({"status": "success", "message": "Inventory updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[Error - Edit Inventory] {e}")
        return jsonify({"status": "error", "message": "Failed to update inventory.", "error": str(e)}), 500

# Delete Product
@inventory_bp.route("/delete", methods=["DELETE"])
def delete_inventory():
    """Delete a product and its inventory entry."""
    try:
        product_id = request.args.get("product_id")
        if not product_id:
            return jsonify({"status": "error", "message": "product_id required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"status": "error", "message": "Product not found"}), 404

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
def export_inventory():
    """Download all inventory for a shop as Excel."""
    try:
        shop_id = request.args.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400

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
