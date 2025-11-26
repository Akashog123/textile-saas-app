from flask import Blueprint, jsonify, request
from models.model import db, ProductCatalog
from utils.auth_utils import token_required
import pandas as pd
from pathlib import Path
import random

catalog_bp = Blueprint("catalog", __name__)


# LOAD CATALOG INTO DATABASE
@catalog_bp.route("/load", methods=["POST"])
@token_required
def load_catalog(current_user):
    """
    Dangerous operation: Clears and reloads entire product catalog.
    Should only be used for initial setup or maintenance.
    Requires authentication to prevent unauthorized use.
    """
    try:
        # Dataset path (relative to backend folder)
        base_path = Path(__file__).resolve().parent.parent / "datasets" / "fashion-dataset"
        catalog_path = base_path / "catalog.csv"

        if not catalog_path.exists():
            return jsonify({"status": "error", "message": f"Catalog file not found at {catalog_path}"}), 404

        # Read CSV using pandas
        df = pd.read_csv(catalog_path, on_bad_lines='skip')

        # Clear old records to prevent duplicates
        ProductCatalog.query.delete()

        # Insert records in batches for speed
        batch_size = 500
        products = []
        for _, row in df.iterrows():
            product = ProductCatalog(
                product_id=str(row.get("product_id")),
                product_name=row.get("product_name"),
                category=row.get("category"),
                subcategory=row.get("subcategory"),
                article_type=row.get("article_type"),
                color=row.get("color"),
                gender=row.get("gender"),
                season=row.get("season"),
                year=int(row["year"]) if not pd.isna(row["year"]) else None,
                usage=row.get("usage"),
                image_url=row.get("image_url"),
            )
            product.price = random.randint(499, 2999)
            products.append(product)

            if len(products) >= batch_size:
                db.session.bulk_save_objects(products)
                db.session.commit()
                products = []

        if products:
            db.session.bulk_save_objects(products)
            db.session.commit()

        return jsonify({"status": "success", "message": f"Catalog loaded successfully ({len(df)} products)."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# VIEW CATALOG PRODUCTS
@catalog_bp.route("/view", methods=["GET"])
def view_catalog():
    try:
        limit = int(request.args.get("limit", 50))
        products = ProductCatalog.query.limit(limit).all()
        return jsonify([p.to_dict() for p in products]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


#  SEARCH / FILTER PRODUCTS
@catalog_bp.route("/search", methods=["GET"])
def search_catalog():
    try:
        query = ProductCatalog.query

        # Optional filters
        category = request.args.get("category")
        color = request.args.get("color")
        gender = request.args.get("gender")
        season = request.args.get("season")
        usage = request.args.get("usage")
        keyword = request.args.get("keyword")

        if not keyword:
            return jsonify({
                "status": "error",
                "message": "Query parameter 'keyword' is required to search the catalog"
            }), 400

        if category:
            query = query.filter(ProductCatalog.category.ilike(f"%{category}%"))
        if color:
            query = query.filter(ProductCatalog.color.ilike(f"%{color}%"))
        if gender:
            query = query.filter(ProductCatalog.gender.ilike(f"%{gender}%"))
        if season:
            query = query.filter(ProductCatalog.season.ilike(f"%{season}%"))
        if usage:
            query = query.filter(ProductCatalog.usage.ilike(f"%{usage}%"))
        if keyword:
            query = query.filter(ProductCatalog.product_name.ilike(f"%{keyword}%"))

        results = query.limit(100).all()

        return jsonify({
            "status": "success",
            "total_results": len(results),
            "products": [p.to_dict() for p in results]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
