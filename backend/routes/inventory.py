from flask import Blueprint, jsonify, request, send_file
from models.model import db, Product, Inventory, SalesData, ProductCatalog
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
                    "name": p.name or "Unknown Product",
                    "category": p.category or "General",
                    "price": float(p.price or 0),
                    "stock": inv.qty_available if inv else 0,
                    "sku": p.sku or f"AUTO-{p.id}",
                    "rating": round(p.rating or 4.0, 1),
                    "image": p.image_url or "https://placehold.co/400x300?text=No+Image",
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
        shop_id = request.form.get("shop_id")

        if not file or not shop_id:
            return jsonify({"status": "error", "message": "Missing file or shop_id"}), 400

        filename = file.filename.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "File must be .csv or .xlsx"}), 400

        # Convert all columns to lowercase for validation
        df.columns = [c.lower() for c in df.columns]

        required_cols = {"name", "category", "price", "stock", "sku"}
        if not required_cols.issubset(set(df.columns)):
            return jsonify({"status": "error", "message": f"File must contain columns: {', '.join(required_cols)}"}), 400

        added, updated = 0, 0
        for _, row in df.iterrows():
            sku = str(row.get("sku", "")).strip()
            name = row.get("name", "Unnamed Product")
            category = row.get("category", "General")
            price = float(row.get("price", 0))
            stock = int(row.get("stock", 0))

            if not sku:
                continue

            product = Product.query.filter_by(sku=sku, shop_id=shop_id).first()
            if product:
                product.name = name
                product.category = category
                product.price = price
                inv = Inventory.query.filter_by(product_id=product.id).first()
                if inv:
                    inv.qty_available = stock
                else:
                    db.session.add(Inventory(product_id=product.id, qty_available=stock))
                updated += 1
            else:
                new_product = Product(name=name, category=category, price=price, sku=sku, shop_id=shop_id)
                db.session.add(new_product)
                db.session.flush()
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
