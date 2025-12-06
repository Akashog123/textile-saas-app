import os
import hashlib
import time
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file
from io import StringIO, BytesIO
from utils.auth_utils import token_required, roles_required, check_shop_ownership
from utils.validation import validate_file_upload
from utils.performance_utils import performance_monitor
from utils.csv_templates import validate_columns, SALES_COLUMNS
from models.model import db, Product, Inventory, SalesData, Shop, User, SalesUploadLog, ShopImage, CachedAIInsight
from config import Config
from services.ai_service import (
    forecast_trends,
    generate_demand_summary,
    generate_recommendation,
    generate_production_priorities,
)
from services.sales_analytics_service import get_sales_analytics_service, invalidate_shop_cache

shop_bp = Blueprint("shop", __name__)
INSTANCE_FOLDER = Config.DATA_DIR

# AI Insight Cache TTL (24 hours)
AI_INSIGHT_TTL_HOURS = 24

def _default_dashboard_data():
    return {
        "weekly_sales": "₹0",
        "pending_reorders": 0,
        "total_orders": 0,
        "customer_rating": 0.0,
        "trend_chart": [],
        "ai_insights": [],
        "forecast": [],
        "reorder_suggestions": {},
        "production_priorities": [],
        "top_selling": [],
        "underperforming": [],
        "demand_summary": "No sales data recorded yet. Sales analytics will appear once you start recording sales.",
        "recommendation": "Add products to your inventory and upload sales data to unlock AI-powered insights and recommendations."
    }


def _invalidate_db_cache(shop_id):
    """
    Invalidate all cached insights and forecasts for a shop in the database.
    This should be called whenever new sales data is uploaded.
    """
    try:
        # Delete all cached insights for this shop
        CachedAIInsight.query.filter_by(shop_id=shop_id).delete()
        db.session.commit()
        print(f"[Cache Invalidate] Cleared DB cache for shop_id={shop_id}")
    except Exception as e:
        db.session.rollback()
        print(f"[Cache Invalidate Error] Failed to clear DB cache for shop_id={shop_id}: {e}")


def _load_sales_dataframe(path):
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if df.empty:
            return None
        df.columns = [c.lower() for c in df.columns]
        if "date" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.dropna(subset=["date"], inplace=True)
        if df.empty:
            return None
        return df
    except Exception as exc:
        print(f"[Sales File Load Error] {exc}")
        return None


# GET: AI-POWERED SHOP DASHBOARD + AUTO NEXT-MONTH FORECAST
@shop_bp.route("/dashboard", methods=["GET"])
@token_required
def shop_dashboard(current_user):
    """
    AI-powered shop dashboard
    - Reads uploaded monthly CSV
    - Generates analytics & AI insights
    - Creates next-month synthetic forecast automatically
    """
    shop_id = request.args.get("shop_id", type=int)
    if not shop_id:
        return jsonify({"status": "error", "message": "shop_id is required."}), 400
    
    # Validate ownership
    if not check_shop_ownership(current_user.get("id"), shop_id):
        return jsonify({"status": "error", "message": "You don't have permission to access this shop"}), 403

    # Get shop's actual rating from database
    shop = Shop.query.get(shop_id)
    actual_rating = round(shop.rating or 0.0, 1) if shop else 0.0

    sales_path = os.path.join(INSTANCE_FOLDER, f"sales_shop_{shop_id}.csv")
    df = _load_sales_dataframe(sales_path)
    
    # Check if shop has any products in inventory
    product_count = Product.query.filter_by(shop_id=shop_id, is_active=True).count()
    has_inventory = product_count > 0

    if df is None or not has_inventory:
        default_data = _default_dashboard_data()
        default_data["customer_rating"] = actual_rating
        default_data["shop_name"] = shop.name if shop else "Shop"
        
        if not has_inventory:
            info_message = "Welcome! Start by adding products to your inventory. Once you have products and sales, your dashboard analytics will appear here."
        else:
            info_message = f"You have {product_count} products in inventory. Upload sales data to see analytics, forecasts, and AI-powered recommendations."
        
        return jsonify({
            "status": "success",
            "data": default_data,
            "info": info_message
        }), 200

    try:
        # Load & Clean Data
        df["revenue"] = pd.to_numeric(df.get("revenue", 0), errors="coerce").fillna(0)
        df["quantity_sold"] = pd.to_numeric(df.get("quantity_sold", 0), errors="coerce").fillna(0)

        # Time Windows
        now = datetime.now()
        last_7_days = df[df["date"] >= now - timedelta(days=7)]
        prev_week = df[
            (df["date"] < now - timedelta(days=7)) &
            (df["date"] >= now - timedelta(days=14))
        ]

        # Weekly Metrics
        weekly_sales = last_7_days["revenue"].sum()
        prev_sales = prev_week["revenue"].sum()
        growth = ((weekly_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
        total_orders = len(df)

        # Weekly Trend Chart
        trend_chart = (
            last_7_days.groupby(last_7_days["date"].dt.day_name())["revenue"]
            .sum()
            .reset_index()
            .rename(columns={"date": "day", "revenue": "sales"})
            .to_dict(orient="records")
        )

        # Forecast (Top Fabrics/Categories) - Simple aggregation for dashboard
        if "fabric_type" in df.columns:
            forecast = (
                df.groupby("fabric_type")["revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(3)
                .reset_index()
                .to_dict(orient="records")
            )
        elif "category" in df.columns:
            forecast = (
                df.groupby("category")["revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(3)
                .reset_index()
                .to_dict(orient="records")
            )
        else:
            forecast = []

        # AI Production Priorities
        prod_df = df.rename(columns={"product_name": "Product", "revenue": "Sales", "region": "Region"})
        production_priorities, top_selling, underperforming = generate_production_priorities(prod_df)

        # Reorder Suggestions grouped by Distributor
        # Products WITH a distributor are grouped by distributor name for bulk ordering
        # Products WITHOUT a distributor are grouped as "Unassigned" for manual reorder
        reorder_suggestions = {}
        unassigned_products = []  # Products without a registered distributor
        
        # Get all products for this shop with low stock
        low_stock_products = db.session.query(Product, Inventory).join(
            Inventory, Product.id == Inventory.product_id
        ).filter(
            Product.shop_id == shop_id,
            Inventory.qty_available <= Inventory.safety_stock
        ).all()
        
        for product, inventory in low_stock_products:
            # Get product's primary image URL from database
            product_image_url = product.get_primary_image_url(resolve=True) if hasattr(product, 'get_primary_image_url') else None
            
            product_info = {
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "current_stock": inventory.qty_available,
                "minimum_stock": inventory.safety_stock,
                "reorder_quantity": max(inventory.safety_stock * 2 - inventory.qty_available, 10),
                "category": product.category,
                "price": float(product.price),
                "distributor_id": product.distributor_id,
                "has_distributor": product.distributor_id is not None,
                "image": product_image_url
            }
            
            # Group by distributor if assigned, otherwise add to unassigned list
            if product.distributor_id and product.distributor:
                distributor_name = product.distributor.full_name
                distributor_key = f"{distributor_name} (ID: {product.distributor_id})"
                
                if distributor_key not in reorder_suggestions:
                    reorder_suggestions[distributor_key] = {
                        "distributor_id": product.distributor_id,
                        "distributor_name": distributor_name,
                        "distributor_contact": product.distributor.contact,
                        "distributor_email": product.distributor.email,
                        "products": []
                    }
                reorder_suggestions[distributor_key]["products"].append(product_info)
            else:
                unassigned_products.append(product_info)
        
        # Add unassigned products as a separate group if any exist
        if unassigned_products:
            reorder_suggestions["Unassigned (Manual Reorder)"] = {
                "distributor_id": None,
                "distributor_name": "No Distributor Assigned",
                "distributor_contact": None,
                "distributor_email": None,
                "products": unassigned_products,
                "note": "These products don't have a registered distributor. You can assign one via inventory management or reorder manually."
            }
        
        # Calculate total pending reorders count
        total_pending_reorders = sum(
            len(group["products"]) if isinstance(group, dict) else len(group) 
            for group in reorder_suggestions.values()
        )

        # Generate Insights using helper
        insights_data = _generate_insights(df, shop_id=shop_id, has_inventory=True)
        
        return jsonify({
            "status": "success",
            "data": {
                "shop_name": shop.name if shop else "Shop",
                "weekly_sales": f"₹{weekly_sales:,.2f}",
                "pending_reorders": total_pending_reorders,
                "total_orders": total_orders,
                "customer_rating": actual_rating,
                "growth": f"{growth:+.1f}%",
                "trend_chart": trend_chart,
                "ai_insights": insights_data["ai_insights"],
                "forecast": forecast,
                "reorder_suggestions": reorder_suggestions,
                "production_priorities": production_priorities,
                "top_selling": top_selling,
                "underperforming": underperforming,
                "demand_summary": insights_data["demand_summary"],
                "recommendation": insights_data["recommendation"]
            }
        }), 200

    except pd.errors.EmptyDataError:
        # Empty CSV file - not an error, just no data
        print(f"[Dashboard] Empty sales data for shop {shop_id}")
        default_data = _default_dashboard_data()
        default_data["customer_rating"] = actual_rating
        return jsonify({
            "status": "success",
            "data": default_data,
            "info": "No sales records found. Upload sales data to see analytics."
        }), 200
    except (KeyError, ValueError) as e:
        # Data format issues
        print(f"[Dashboard Data Error] {e}")
        default_data = _default_dashboard_data()
        default_data["customer_rating"] = actual_rating
        return jsonify({
            "status": "success",
            "data": default_data,
            "warning": "Sales data format issue detected. Please verify the uploaded sheet has required columns (date, revenue, quantity_sold)."
        }), 200
    except Exception as e:
        # Unexpected errors - log but don't alarm user
        print(f"[Dashboard Error] {e}")
        import traceback
        traceback.print_exc()
        default_data = _default_dashboard_data()
        default_data["customer_rating"] = actual_rating
        return jsonify({
            "status": "success",
            "data": default_data
            # No warning - don't show error to user for unexpected issues
        }), 200

def _generate_insights(df, shop_id=None, force_refresh=False, has_inventory=True):
    """Helper to generate AI insights from sales dataframe.
    
    Caches insights in DB to avoid redundant AI API calls.
    Invalidated when new sales data is uploaded (force_refresh=True).
    """
    try:
        # Check if inventory exists
        if not has_inventory:
            logging.info("[Insights] Skipping AI generation - no inventory data")
            return {
                "ai_insights": [],
                "demand_summary": "Inventory data missing. Please add products to your inventory to enable AI insights.",
                "recommendation": "Add products to your inventory to unlock AI-powered recommendations."
            }

        # Check for cached insights first (unless force refresh requested)
        if shop_id and not force_refresh:
            try:
                cached = CachedAIInsight.query.filter_by(
                    shop_id=shop_id,
                    insight_type='dashboard',
                    is_stale=False
                ).first()
                
                if cached and cached.expires_at and cached.expires_at > datetime.now():
                    logging.info(f"[Insights] Using cached insights for shop {shop_id}")
                    return {
                        "ai_insights": json.loads(cached.insights_json) if cached.insights_json else [],
                        "demand_summary": cached.demand_summary or "",
                        "recommendation": cached.recommendation or "",
                        "cached": True
                    }
            except Exception as cache_read_err:
                logging.warning(f"[Insights] Cache read failed: {cache_read_err}")
        
        # Early return if DataFrame is empty or too small
        if df is None or df.empty or len(df) < 3:
            logging.info("[Insights] Skipping AI generation - insufficient data rows")
            return {
                "ai_insights": [],
                "demand_summary": "Not enough sales data to generate insights. Please upload more sales records.",
                "recommendation": "Upload at least a week of sales data to unlock AI-powered recommendations."
            }
        
        # Ensure revenue exists
        if "revenue" not in df.columns:
            # Try to calculate if quantity and price exist
            if "quantity_sold" in df.columns and "selling_price" in df.columns:
                df["revenue"] = df["quantity_sold"] * df["selling_price"]
            else:
                df["revenue"] = 0

        # Calculate basic metrics for context
        total_revenue = float(df["revenue"].sum())
        
        # Skip AI if total revenue is negligible (no meaningful data)
        if total_revenue < 1:
            logging.info("[Insights] Skipping AI generation - zero or negligible revenue")
            return {
                "ai_insights": [],
                "demand_summary": "No revenue data found. Please ensure your sales data includes revenue information.",
                "recommendation": "Upload sales data with revenue/price information to enable AI insights."
            }
        
        # Summarize by fabric/category for top item
        if "fabric_type" in df.columns:
            top_items = df.groupby("fabric_type")["revenue"].sum().sort_values(ascending=False)
        elif "category" in df.columns:
            top_items = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
        else:
            top_items = pd.Series()
            
        top_item = top_items.index[0] if not top_items.empty else "General"
        
        # AI Demand Summary & Recommendations
        region_summary = (
            df.groupby("region")["revenue"].sum().to_dict()
            if "region" in df.columns else {}
        )
        if not region_summary:
            region_summary = {"Overall": total_revenue}

        trending_products = (
            df.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(5).to_dict()
            if "product_name" in df.columns else {}
        )
        if not trending_products:
            trending_products = {top_item: total_revenue}

        demand_summary = generate_demand_summary(
            region_data=region_summary,
            top_product=top_item,
        )
        
        recommendation = generate_recommendation(
            region_data=region_summary,
            trending_products=trending_products,
        )
        
        # Construct AI Insights list
        ai_insights = [
            {
                "title": f"Strong demand for {top_item}",
                "impact": "Positive",
                "category": "Trend",
                "description": demand_summary
            },
            {
                "title": "Restocking Recommendation",
                "impact": "Action",
                "category": "Inventory",
                "description": recommendation
            }
        ]
        
        result = {
            "ai_insights": ai_insights,
            "demand_summary": demand_summary,
            "recommendation": recommendation
        }
        
        # Save to DB cache if shop_id provided (for future requests)
        if shop_id:
            try:
                cached = CachedAIInsight.query.filter_by(
                    shop_id=shop_id,
                    insight_type='dashboard'
                ).first()
                
                expires_at = datetime.now() + timedelta(hours=AI_INSIGHT_TTL_HOURS)
                
                if cached:
                    cached.insights_json = json.dumps(ai_insights)
                    cached.demand_summary = demand_summary
                    cached.recommendation = recommendation
                    cached.is_stale = False
                    cached.expires_at = expires_at
                    cached.updated_at = datetime.now()
                else:
                    cached = CachedAIInsight(
                        shop_id=shop_id,
                        insight_type='dashboard',
                        insights_json=json.dumps(ai_insights),
                        demand_summary=demand_summary,
                        recommendation=recommendation,
                        is_stale=False,
                        expires_at=expires_at
                    )
                    db.session.add(cached)
                
                db.session.commit()
                logging.info(f"[Insights] Cached insights for shop {shop_id}")
            except Exception as cache_err:
                db.session.rollback()
                logging.warning(f"[Insights] Failed to cache (non-blocking): {cache_err}")
        
        return result
        
    except Exception as e:
        print(f"[Insight Generation Error] {e}")
        return {
            "ai_insights": [],
            "demand_summary": "Could not generate summary",
            "recommendation": "Could not generate recommendation"
        }

# Upload Sales CSV
@shop_bp.route("/upload_sales_data", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def upload_sales_data(current_user):
    start_time = time.perf_counter()
    log_entry = None
    try:
        shop_id_raw = request.form.get("shop_id")
        file = request.files.get("file")
        if not shop_id_raw or not file:
            return jsonify({"status": "error", "message": "Missing shop_id or file."}), 400

        try:
            shop_id = int(shop_id_raw)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "Invalid shop_id"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to manage this shop"}), 403
        
        # Validate file upload (supports CSV/XLS/XLSX)
        allowed_exts = ['.csv', '.xlsx', '.xls']
        is_valid, message = validate_file_upload(file, allowed_exts, max_size_mb=16)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400

        file_hash = hashlib.sha256(file_bytes).hexdigest()
        duplicate_log = SalesUploadLog.query.filter_by(
            shop_id=shop_id,
            file_hash=file_hash,
            status='completed'
        ).order_by(SalesUploadLog.completed_at.desc()).first()

        log_entry = SalesUploadLog(
            shop_id=shop_id,
            file_name=file.filename,
            file_hash=file_hash,
            status='duplicate' if duplicate_log else 'in_progress',
            duplicate_of=duplicate_log.id if duplicate_log else None
        )
        db.session.add(log_entry)
        db.session.flush()

        if duplicate_log:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_entry.completed_at = datetime.utcnow()
            log_entry.duration_ms = duration_ms
            log_entry.sla_breached = duration_ms > SalesUploadLog.SLA_LIMIT_MS
            log_entry.message = f"Duplicate of upload #{duplicate_log.id}"
            db.session.commit()
            return jsonify({
                "status": "duplicate",
                "message": "This sales file matches a previously processed upload.",
                "duplicate_of": duplicate_log.id,
                "upload_log": log_entry.to_dict()
            }), 409

        ext = os.path.splitext(file.filename)[1].lower()
        buffer = BytesIO(file_bytes)
        if ext == '.csv':
            df = pd.read_csv(buffer)
        else:
            df = pd.read_excel(buffer)

        # Normalize columns to lowercase
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Validate columns using centralized template
        is_valid, missing, message = validate_columns(df.columns.tolist(), "sales")
        if not is_valid:
            return jsonify({
                "status": "error", 
                "message": message,
                "hint": "Download the template from GET /api/v1/inventory/template/sales"
            }), 400

        # Calculate revenue for insights
        df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0)
        df["selling_price"] = pd.to_numeric(df["selling_price"], errors="coerce").fillna(0)
        df["revenue"] = df["quantity_sold"] * df["selling_price"]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.dropna(subset=["date"], inplace=True)

        # Process each row and update inventory
        stock_updates = []
        matched_products_count = 0
        for _, row in df.iterrows():
            try:
                sku = row.get("sku", "")
                quantity_sold = int(row.get("quantity_sold", 0) or 0)
                sale_date = row.get("date")
                if pd.isna(sale_date):
                    continue
                if hasattr(sale_date, "date"):
                    sale_date = sale_date.date()
                
                # Find product by SKU and shop_id
                product = Product.query.filter_by(sku=sku, shop_id=shop_id).first()
                if not product:
                    continue
                
                matched_products_count += 1
                
                # Get inventory record
                inventory = Inventory.query.filter_by(product_id=product.id).first()
                
                # Upsert into SalesData for delta tracking
                sales_entry = SalesData.query.filter_by(
                    shop_id=shop_id,
                    product_id=product.id,
                    date=sale_date
                ).first()

                previous_qty = sales_entry.quantity_sold if sales_entry else 0
                delta_qty = quantity_sold - previous_qty

                if sales_entry:
                    sales_entry.quantity_sold = quantity_sold
                    sales_entry.revenue = float(row.get("revenue", 0))
                else:
                    sales_entry = SalesData(
                        date=sale_date,
                        product_id=product.id,
                        shop_id=shop_id,
                        quantity_sold=quantity_sold,
                        revenue=float(row.get("revenue", 0)),
                        fabric_type=row.get("category") or row.get("fabric_type"),
                        region=row.get("region")
                    )
                    db.session.add(sales_entry)

                if inventory:
                    # Track that we received sales data for this product
                    inventory.last_sales_data_at = datetime.utcnow()

                if not inventory or delta_qty == 0:
                    continue

                # Adjust stock based on delta (positive delta reduces stock, negative increases)
                old_stock = inventory.qty_available
                new_stock = max(0, old_stock - delta_qty)
                inventory.qty_available = new_stock
                
                # Update total_sold to track cumulative sales quantity
                inventory.total_sold = (inventory.total_sold or 0) + max(0, delta_qty)
                
                stock_updates.append({
                    "product_name": product.name,
                    "sku": sku,
                    "sale_date": sale_date.isoformat(),
                    "delta_quantity": -delta_qty,
                    "recorded_quantity": quantity_sold,
                    "old_stock": old_stock,
                    "new_stock": new_stock
                })
                
            except Exception as e:
                print(f"[Sales Upload] Error processing row: {e}")
                continue

        # Save normalized CSV for downstream analytics
        save_path = os.path.join(INSTANCE_FOLDER, f"sales_shop_{shop_id}.csv")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False)
        
        # Invalidate ALL caches for this shop (insights, forecasts, analytics)
        invalidate_shop_cache(shop_id)
        _invalidate_db_cache(shop_id)
        
        # Check if shop has any products in inventory
        product_count = Product.query.filter_by(shop_id=shop_id, is_active=True).count()
        has_inventory = product_count > 0

        # Generate fresh AI Insights (force_refresh=True to bypass cache)
        insights_data = _generate_insights(df, shop_id=shop_id, force_refresh=True, has_inventory=has_inventory)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry.rows_processed = len(df)
        log_entry.completed_at = datetime.utcnow()
        log_entry.duration_ms = duration_ms
        log_entry.status = 'completed'
        log_entry.message = f"Updated stock for {len(stock_updates)} products."
        log_entry.sla_breached = duration_ms > SalesUploadLog.SLA_LIMIT_MS
        
        db.session.commit()
        
        print(f"[Sales Upload] Processed {len(stock_updates)} stock updates for shop {shop_id}")
        
        warning_msg = None
        if matched_products_count == 0 and len(df) > 0:
            warning_msg = "Sales data uploaded, but no matching products found in inventory. Please upload inventory with matching SKUs to track stock and sales history."

        return jsonify({
            "status": "success", 
            "message": f"Sales data uploaded successfully! Updated stock for {len(stock_updates)} products.",
            "warning": warning_msg,
            "stock_updates": stock_updates,
            "ai_insights": insights_data["ai_insights"],
            "demand_summary": insights_data["demand_summary"],
            "recommendation": insights_data["recommendation"],
            "upload_log": log_entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        if log_entry:
            try:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                log_entry.status = 'failed'
                log_entry.completed_at = datetime.utcnow()
                log_entry.duration_ms = duration_ms
                log_entry.sla_breached = duration_ms > SalesUploadLog.SLA_LIMIT_MS
                log_entry.message = str(e)[:250]
                db.session.add(log_entry)
                db.session.commit()
            except Exception as log_err:
                db.session.rollback()
                print(f"[Sales Upload Log Error] {log_err}")
        print(f"[Upload Error] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@shop_bp.route("/upload_sales_data/logs", methods=["GET"])
@token_required
@roles_required('shop_owner', 'shop_manager')
def get_sales_upload_logs(current_user):
    try:
        shop_id = request.args.get("shop_id", type=int)
        limit = request.args.get("limit", default=5, type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400

        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to access this shop"}), 403

        logs = (SalesUploadLog.query
                .filter_by(shop_id=shop_id)
                .order_by(SalesUploadLog.started_at.desc())
                .limit(min(limit, 25))
                .all())

        return jsonify({
            "status": "success",
            "count": len(logs),
            "logs": [log.to_dict() for log in logs]
        })
    except Exception as e:
        print(f"[Sales Upload Logs Error] {e}")
        return jsonify({"status": "error", "message": "Failed to fetch upload logs"}), 500


# Get Distributors for Search
@shop_bp.route("/distributors", methods=["GET"])
@token_required
def get_distributors(current_user):
    """Get list of distributors for shop inquiry with search functionality"""
    try:
        search = request.args.get("search", "").strip()
        
        # Query distributors with optional search
        query = User.query.filter_by(role="distributor", approved=True)
        
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.city.ilike(f"%{search}%"),
                    User.state.ilike(f"%{search}%")
                )
            )
        
        distributors = query.limit(20).all()
        
        result = []
        for dist in distributors:
            result.append({
                "id": dist.id,
                "username": dist.username,
                "full_name": dist.full_name,
                "email": dist.email,
                "city": dist.city or "",
                "state": dist.state or "",
                "contact": dist.contact or ""
            })
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
        
    except Exception as e:
        print(f"[Distributors Error] {e}")
        return jsonify({"status": "error", "message": "Failed to fetch distributors"}), 500


# =============================================================================
# SALES ANALYTICS ENDPOINTS
# =============================================================================

@shop_bp.route("/sales-summary", methods=["GET"])
@token_required
def get_sales_summary(current_user):
    """
    Get comprehensive weekly sales summary for last 7 days.
    Returns detailed metrics, daily breakdown, top products, and insights.
    """
    try:
        shop_id = request.args.get("shop_id", type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Get analytics service for this shop
        analytics = get_sales_analytics_service(shop_id)
        summary = analytics.get_weekly_sales_summary()
        
        return jsonify({
            "status": "success",
            "data": summary
        }), 200
        
    except Exception as e:
        logging.exception(f"[Sales Summary Error] Shop {request.args.get('shop_id')}")
        return jsonify({
            "status": "error",
            "message": "Failed to generate sales summary",
            "error": str(e)
        }), 500


@shop_bp.route("/quarterly-forecast", methods=["GET"])
@token_required
def get_quarterly_forecast(current_user):
    """
    Get next quarter (90 days) demand forecast.
    Returns weekly and monthly predictions with confidence intervals.
    """
    try:
        shop_id = request.args.get("shop_id", type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Get analytics service for this shop
        analytics = get_sales_analytics_service(shop_id)
        forecast = analytics.get_quarterly_demand_forecast()
        
        return jsonify({
            "status": "success",
            "data": forecast
        }), 200
        
    except Exception as e:
        logging.exception(f"[Quarterly Forecast Error] Shop {request.args.get('shop_id')}")
        return jsonify({
            "status": "error",
            "message": "Failed to generate quarterly forecast",
            "error": str(e)
        }), 500


@shop_bp.route("/sales-growth-trend", methods=["GET"])
@token_required
def get_sales_growth_trend(current_user):
    """
    Get sales growth trend data for charting.
    
    Query params:
        shop_id: Shop ID (required)
        period: 'weekly', 'monthly', or 'yearly' (default: 'weekly')
    
    Returns:
        Chart data with labels, values, SVG paths, and growth metrics
    """
    try:
        shop_id = request.args.get("shop_id", type=int)
        period = request.args.get("period", "weekly")
        
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate period
        if period not in ['weekly', 'monthly', 'yearly']:
            return jsonify({"status": "error", "message": "period must be 'weekly', 'monthly', or 'yearly'"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Access denied"}), 403
        
        # Get analytics service for this shop
        analytics = get_sales_analytics_service(shop_id)
        trend_data = analytics.get_sales_growth_trend(period)
        
        return jsonify({
            "status": "success",
            "data": trend_data
        }), 200
        
    except Exception as e:
        logging.exception(f"[Sales Growth Trend Error] Shop {request.args.get('shop_id')}")
        return jsonify({
            "status": "error",
            "message": "Failed to generate sales growth trend",
            "error": str(e)
        }), 500


# Next Quarter Demand Forecast
@shop_bp.route("/demand-forecast", methods=["GET"])
@token_required
def get_demand_forecast(current_user):
    """
    Generate next quarter demand forecast using Prophet on database sales data.
    
    NOTE: The newer /quarterly-forecast endpoint is preferred. This endpoint
    is maintained for backward compatibility but now uses database data
    instead of CSV files.
    """
    try:
        shop_id = request.args.get("shop_id")
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required"}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to access this shop"}), 403

        # Use database instead of CSV files
        from sqlalchemy import func
        
        # Query sales data from database
        sales_records = db.session.query(
            func.date(SalesData.date).label('date'),
            func.sum(SalesData.quantity_sold).label('quantity_sold')
        ).filter(
            SalesData.shop_id == int(shop_id)
        ).group_by(
            func.date(SalesData.date)
        ).order_by(
            func.date(SalesData.date)
        ).all()
        
        # Check if we have enough data to run Prophet
        if not sales_records or len(sales_records) < 7:
            logging.info(f"[Demand Forecast] Skipping Prophet - insufficient data ({len(sales_records) if sales_records else 0} days)")
            return jsonify({
                "status": "success",
                "message": "Not enough sales data for forecasting. Need at least 7 days of data.",
                "forecast": [],
                "data_points": len(sales_records) if sales_records else 0
            }), 200
        
        # Convert to DataFrame for Prophet
        df = pd.DataFrame([{
            "date": r.date,
            "quantity_sold": float(r.quantity_sold or 0)
        } for r in sales_records])
        
        df["date"] = pd.to_datetime(df["date"])
        daily_sales = df.rename(columns={"date": "Date", "quantity_sold": "Sales"})
        
        # Generate Forecast using Prophet (via AI Service)
        forecast_data = forecast_trends(daily_sales)
        
        # Format for frontend
        formatted_forecast = []
        for item in forecast_data:
            formatted_forecast.append({
                "date": item["ds"].strftime("%Y-%m-%d") if hasattr(item["ds"], "strftime") else str(item["ds"]),
                "predicted_sales": int(item["yhat"]),
                "confidence": "High"
            })
        
        return jsonify({
            "status": "success",
            "message": "Demand forecast generated successfully",
            "forecast": formatted_forecast,
            "quarter": "Next Quarter",
            "generated_at": datetime.now().isoformat(),
            "data_source": "database",
            "data_points": len(sales_records)
        }), 200
        
    except Exception as e:
        logging.error(f"[Demand Forecast Error] {e}")
        return jsonify({"status": "error", "message": "Failed to generate demand forecast"}), 500


# Export Sales Report
@shop_bp.route("/sales/export", methods=["GET"])
@token_required
def export_sales(current_user):
    try:
        shop_id = request.args.get("shop_id", type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required."}), 400
        
        # Validate ownership
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "You don't have permission to export this shop's data"}), 403

        sales_path = os.path.join(INSTANCE_FOLDER, f"sales_shop_{shop_id}.csv")
        if not os.path.exists(sales_path):
            return jsonify({"status": "error", "message": "No sales data found."}), 404

        return send_file(
            sales_path,
            as_attachment=True,
            download_name=f"shop_{shop_id}_sales_report.csv",
            mimetype="text/csv"
        )
    except Exception as e:
        print(f"[EXPORT ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500




# ------------------------------------------------------------------
# Owner endpoints: list, create, get, update, delete
# All in this file as requested
# ------------------------------------------------------------------

def _serialize_shop(s: Shop):
    """Return a safe dict for frontend consumption."""
    return {
        "id": s.id,
        "shop_name": s.name,
        "name": s.name,
        "description": s.description or "",
        "address": s.address or s.location or "",
        "location": s.location or s.address or "",
        "city": s.city or "",
        "state": s.state or "",
        "contact": getattr(s, "contact", None) or "",
        "gstin": getattr(s, "gstin", None) or "",
        "latitude": float(s.lat) if s.lat is not None else None,
        "longitude": float(s.lon) if s.lon is not None else None,
        "image": getattr(s, "image_url", None) or None,
        "created_at": s.created_at.isoformat() if getattr(s, "created_at", None) else None,
        "rating": round(s.rating or 0.0, 1),
    }

# GET: Owner's Shops
@shop_bp.route("/my-shops", methods=["GET"])
@token_required
def my_shops_list(current_user):
    try:
        user_id = getattr(current_user, "id", None) or (current_user.get("id") if isinstance(current_user, dict) else None)
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid user"}), 400

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
        if per_page > 200:
            per_page = 200

        q = Shop.query.filter_by(owner_id=user_id).order_by(Shop.created_at.desc())
        try:
            paged = q.paginate(page=page, per_page=per_page, error_out=False)
            items = paged.items
            total = paged.total
        except Exception:
            items = q.limit(per_page).offset((page - 1) * per_page).all()
            total = q.count()

        shops_out = [_serialize_shop(s) for s in items]

        return jsonify({
            "status": "success",
            "shops": shops_out,
            "count": len(shops_out),
            "page": page,
            "per_page": per_page,
            "total": total
        }), 200

    except Exception:
        logging.exception("Error fetching owner shops")
        return jsonify({"status": "error", "message": "Failed to fetch your shops"}), 500


# POST: Create new shop
@shop_bp.route("/my-shops", methods=["POST"])
@token_required
def create_my_shop(current_user):
    """
    Create a shop owned by the authenticated user.
    Expected JSON fields (recommended):
      - name (required)
      - description, address, location, city, state, contact, gstin
      - latitude (float), longitude (float)
    """
    try:
        payload = request.get_json(force=True, silent=True) or {}
        name = (payload.get("name") or payload.get("shop_name") or "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Shop name is required"}), 400

        user_id = getattr(current_user, "id", None) or (current_user.get("id") if isinstance(current_user, dict) else None)
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid user"}), 400

        # build model
        s = Shop(
            name=name,
            description=payload.get("description"),
            address=payload.get("address") or payload.get("location"),
            location=payload.get("location") or payload.get("address"),
            city=payload.get("city"),
            state=payload.get("state"),
            contact=payload.get("contact"),
            gstin=payload.get("gstin"),
            image_url=payload.get("image"),
            owner_id=user_id
        )

        # optional numeric coords
        lat = payload.get("latitude")
        lon = payload.get("longitude")
        try:
            s.lat = float(lat) if lat is not None and str(lat) != "" else None
        except Exception:
            s.lat = None
        try:
            s.lon = float(lon) if lon is not None and str(lon) != "" else None
        except Exception:
            s.lon = None

        db.session.add(s)
        db.session.commit()

        return jsonify({"status": "success", "shop": _serialize_shop(s)}), 201

    except Exception:
        logging.exception("Error creating shop")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to create shop"}), 500


# PUT: Update an existing shop (owner-only)
@shop_bp.route("/my-shops/<int:shop_id>", methods=["PUT", "PATCH"])
@token_required
def update_my_shop(current_user, shop_id):
    """
    Update shop fields. Owner only.
    Accepts same fields as create.
    """
    try:
        user_id = getattr(current_user, "id", None) or (current_user.get("id") if isinstance(current_user, dict) else None)
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid user"}), 400

        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404

        if int(shop.owner_id) != int(user_id):
            return jsonify({"status": "error", "message": "Not authorized to update this shop"}), 403

        payload = request.get_json(force=True, silent=True) or {}

        # update only provided fields
        for key_map in [
            ("name", "name"),
            ("shop_name", "name"),
            ("description", "description"),
            ("address", "address"),
            ("location", "location"),
            ("city", "city"),
            ("state", "state"),
            ("contact", "contact"),
            ("gstin", "gstin"),
            ("image", "image_url"),
        ]:
            body_key, model_key = key_map
            if body_key in payload:
                setattr(shop, model_key, payload.get(body_key))

        # coords
        if "latitude" in payload:
            try:
                shop.lat = float(payload.get("latitude")) if payload.get("latitude") not in (None, "") else None
            except Exception:
                shop.lat = None
        if "longitude" in payload:
            try:
                shop.lon = float(payload.get("longitude")) if payload.get("longitude") not in (None, "") else None
            except Exception:
                shop.lon = None

        db.session.add(shop)
        db.session.commit()

        return jsonify({"status": "success", "shop": _serialize_shop(shop)}), 200

    except Exception:
        logging.exception("Error updating shop")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to update shop"}), 500


# DELETE: Delete an owner's shop (owner-only)
@shop_bp.route("/my-shops/<int:shop_id>", methods=["DELETE"])
@token_required
def delete_my_shop(current_user, shop_id):
    try:
        user_id = getattr(current_user, "id", None) or (current_user.get("id") if isinstance(current_user, dict) else None)
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid user"}), 400

        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404

        if int(shop.owner_id) != int(user_id):
            return jsonify({"status": "error", "message": "Not authorized to delete this shop"}), 403

        db.session.delete(shop)
        db.session.commit()

        return jsonify({"status": "success", "message": "Shop deleted"}), 200

    except Exception:
        logging.exception("Error deleting shop")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete shop"}), 500


# ============================================================================
# SHOP IMAGE MANAGEMENT ENDPOINTS
# ============================================================================

MAX_SHOP_IMAGES = 4
SHOP_IMAGES_FOLDER = os.path.join(Config.UPLOAD_FOLDER, "shop_images")
os.makedirs(SHOP_IMAGES_FOLDER, exist_ok=True)


def _get_shop_images(shop_id):
    """Get all images for a shop ordered by ordering field."""
    from models.model import ShopImage
    images = ShopImage.query.filter_by(shop_id=shop_id).order_by(ShopImage.ordering).all()
    return [img.to_dict() for img in images]


# GET: List all images for a shop
@shop_bp.route("/<int:shop_id>/images", methods=["GET"])
def get_shop_images(shop_id):
    """Get all images for a specific shop (public endpoint)."""
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        images = _get_shop_images(shop_id)
        return jsonify({
            "status": "success",
            "shop_id": shop_id,
            "images": images,
            "max_images": MAX_SHOP_IMAGES,
            "can_upload_more": len(images) < MAX_SHOP_IMAGES
        }), 200
    except Exception as e:
        logging.exception("Error fetching shop images")
        return jsonify({"status": "error", "message": "Failed to fetch images"}), 500


# POST: Upload images for a shop (up to 4)
@shop_bp.route("/<int:shop_id>/images", methods=["POST"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'admin')
def upload_shop_images(current_user, shop_id):
    """
    Upload images for a shop. Maximum 4 images allowed per shop.
    Accepts multipart form data with 'images' field (multiple files).
    """
    from models.model import ShopImage
    from werkzeug.utils import secure_filename
    import uuid
    
    try:
        # Validate shop exists and user owns it
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Not authorized to manage this shop"}), 403
        
        # Check existing image count
        existing_count = ShopImage.query.filter_by(shop_id=shop_id).count()
        
        # Get uploaded files
        files = request.files.getlist("images")
        if not files or all(f.filename == '' for f in files):
            return jsonify({"status": "error", "message": "No images provided"}), 400
        
        # Filter out empty files
        files = [f for f in files if f.filename != '']
        
        # Check if adding these would exceed limit
        if existing_count + len(files) > MAX_SHOP_IMAGES:
            remaining = MAX_SHOP_IMAGES - existing_count
            return jsonify({
                "status": "error",
                "message": f"Cannot upload {len(files)} images. Only {remaining} slot(s) remaining (max {MAX_SHOP_IMAGES}).",
                "existing_count": existing_count,
                "max_images": MAX_SHOP_IMAGES,
                "remaining_slots": remaining
            }), 400
        
        # Allowed image extensions
        allowed_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        uploaded_images = []
        
        # Get next ordering value
        max_order = db.session.query(db.func.max(ShopImage.ordering)).filter_by(shop_id=shop_id).scalar() or -1
        
        for idx, file in enumerate(files):
            # Validate file extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_exts:
                continue  # Skip invalid files
            
            # Validate file (check size, type)
            is_valid, message = validate_file_upload(file, allowed_exts, max_size_mb=5)
            if not is_valid:
                continue  # Skip invalid files
            
            # Generate unique filename
            unique_id = uuid.uuid4().hex[:8]
            safe_name = secure_filename(file.filename)
            filename = f"shop_{shop_id}_{unique_id}_{safe_name}"
            filepath = os.path.join(SHOP_IMAGES_FOLDER, filename)
            
            # Save file
            file.seek(0)  # Reset file pointer after validation
            file.save(filepath)
            
            # Create database record
            shop_image = ShopImage(
                shop_id=shop_id,
                url=f"/uploads/shop_images/{filename}",
                alt=f"{shop.name} image {max_order + idx + 2}",
                ordering=max_order + idx + 1
            )
            db.session.add(shop_image)
            uploaded_images.append(shop_image)
        
        if not uploaded_images:
            return jsonify({"status": "error", "message": "No valid images uploaded"}), 400
        
        db.session.commit()
        
        # Return updated image list
        all_images = _get_shop_images(shop_id)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully uploaded {len(uploaded_images)} image(s)",
            "uploaded_count": len(uploaded_images),
            "images": all_images,
            "remaining_slots": MAX_SHOP_IMAGES - len(all_images)
        }), 201
        
    except Exception as e:
        logging.exception("Error uploading shop images")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to upload images"}), 500


# DELETE: Delete a specific shop image
@shop_bp.route("/<int:shop_id>/images/<int:image_id>", methods=["DELETE"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'admin')
def delete_shop_image(current_user, shop_id, image_id):
    """Delete a specific image from a shop."""
    from models.model import ShopImage
    
    try:
        # Validate shop and ownership
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Not authorized to manage this shop"}), 403
        
        # Find the image
        image = ShopImage.query.filter_by(id=image_id, shop_id=shop_id).first()
        if not image:
            return jsonify({"status": "error", "message": "Image not found"}), 404
        
        # Delete physical file if it exists
        if image.url.startswith("/uploads/"):
            filepath = os.path.join(Config.BASE_DIR, image.url.lstrip("/"))
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logging.warning(f"Could not delete image file: {e}")
        
        # Delete database record
        db.session.delete(image)
        db.session.commit()
        
        # Re-order remaining images
        remaining = ShopImage.query.filter_by(shop_id=shop_id).order_by(ShopImage.ordering).all()
        for idx, img in enumerate(remaining):
            img.ordering = idx
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Image deleted successfully",
            "images": _get_shop_images(shop_id),
            "remaining_slots": MAX_SHOP_IMAGES - len(remaining)
        }), 200
        
    except Exception as e:
        logging.exception("Error deleting shop image")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to delete image"}), 500


# PUT: Reorder shop images
@shop_bp.route("/<int:shop_id>/images/reorder", methods=["PUT"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'admin')
def reorder_shop_images(current_user, shop_id):
    """
    Reorder shop images. 
    Expects JSON body: { "image_ids": [3, 1, 2, 4] } where order in array = display order
    """
    from models.model import ShopImage
    
    try:
        # Validate shop and ownership
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Not authorized to manage this shop"}), 403
        
        data = request.get_json()
        if not data or "image_ids" not in data:
            return jsonify({"status": "error", "message": "image_ids array required"}), 400
        
        image_ids = data["image_ids"]
        if not isinstance(image_ids, list):
            return jsonify({"status": "error", "message": "image_ids must be an array"}), 400
        
        # Verify all image IDs belong to this shop
        shop_images = ShopImage.query.filter_by(shop_id=shop_id).all()
        shop_image_ids = {img.id for img in shop_images}
        
        if set(image_ids) != shop_image_ids:
            return jsonify({"status": "error", "message": "Invalid image IDs provided"}), 400
        
        # Update ordering
        for idx, img_id in enumerate(image_ids):
            img = ShopImage.query.get(img_id)
            if img:
                img.ordering = idx
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Images reordered successfully",
            "images": _get_shop_images(shop_id)
        }), 200
        
    except Exception as e:
        logging.exception("Error reordering shop images")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to reorder images"}), 500


# PUT: Set primary/cover image
@shop_bp.route("/<int:shop_id>/images/<int:image_id>/set-primary", methods=["PUT"])
@token_required
@roles_required('shop_owner', 'shop_manager', 'admin')
def set_primary_shop_image(current_user, shop_id, image_id):
    """Set a shop image as the primary/cover image (moves it to position 0)."""
    from models.model import ShopImage
    
    try:
        # Validate shop and ownership
        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"status": "error", "message": "Shop not found"}), 404
        
        if not check_shop_ownership(current_user.get("id"), shop_id):
            return jsonify({"status": "error", "message": "Not authorized to manage this shop"}), 403
        
        # Find the image
        image = ShopImage.query.filter_by(id=image_id, shop_id=shop_id).first()
        if not image:
            return jsonify({"status": "error", "message": "Image not found"}), 404
        
        # Get all images and reorder
        all_images = ShopImage.query.filter_by(shop_id=shop_id).order_by(ShopImage.ordering).all()
        
        # Set the selected image to order 0, shift others
        for img in all_images:
            if img.id == image_id:
                img.ordering = 0
            elif img.ordering < image.ordering:
                img.ordering += 1
        
        # Also update the shop's main image_url to this image
        shop.image_url = image.url
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Primary image updated",
            "images": _get_shop_images(shop_id),
            "primary_image_url": image.url
        }), 200
        
    except Exception as e:
        logging.exception("Error setting primary shop image")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to set primary image"}), 500
