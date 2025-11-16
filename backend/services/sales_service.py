# backend/services/sales_service.py

from models.model import db, Shop, Product, SalesData
from flask import send_file
from io import BytesIO
from datetime import datetime, timedelta
import pandas as pd

# Optional imports (AI/Forecasting)
try:
    from services.ai_service import generate_demand_summary, generate_recommendation
    from services.forecasting_service import (
        forecast_sales,
        compute_regional_summary,
        top_trending_products
    )
except ImportError:
    generate_demand_summary = lambda **kwargs: "AI summary unavailable (module missing)."
    generate_recommendation = lambda **kwargs: "Recommendations unavailable."
    forecast_sales = lambda df: []
    compute_regional_summary = lambda df: []
    top_trending_products = lambda df: []


# Dashboard Metrics
def get_dashboard_metrics(shop_id):
    """Generate dynamic dashboard analytics for a shop (used in shop dashboard)."""
    shop = Shop.query.get(shop_id)
    if not shop:
        raise ValueError("Shop not found.")

    last_30_days = datetime.utcnow() - timedelta(days=30)

    # Correct join and filter (use Product.shop_id, not SalesData.fabric)
    sales_records = (
        db.session.query(SalesData, Product)
        .join(Product, SalesData.product_id == Product.id)
        .filter(Product.shop_id == shop_id, SalesData.date >= last_30_days)
        .order_by(SalesData.date.asc())
        .all()
    )

    if not sales_records:
        return {
            "weekly_sales": "₹0",
            "total_orders": 0,
            "pending_reorders": 0,
            "customer_rating": round(shop.rating or 4.0, 1),
            "weekly_summary": {"summary": "No recent sales data.", "avg_order_value": "₹0"},
            "trend_chart": [],
            "ai_insights": [],
            "reorder_suggestions": []
        }

    # Flatten SalesData + Product
    data = []
    for s, p in sales_records:
        data.append({
            "date": s.date,
            "revenue": float(s.revenue or 0),
            "quantity_sold": int(s.quantity_sold or 0),
            "region": s.region or "Unknown",
            "product": p.name if p else "Unknown"
        })

    # Totals
    total_sales = sum(item["revenue"] for item in data)
    total_orders = sum(item["quantity_sold"] for item in data)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0

    # Weekly trend chart
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    weekly_summary = (
        df.groupby(df["date"].dt.strftime("%a"))["revenue"]
        .sum()
        .reset_index()
        .to_dict(orient="records")
    )

    # AI/Forecast fallback-safe
    try:
        forecast_data = forecast_sales(
            pd.DataFrame([{"Date": d["date"], "Sales": d["revenue"], "Product": d["product"]} for d in data])
        )
        regional_summary = compute_regional_summary(
            pd.DataFrame([{"Date": d["date"], "Region": d["region"], "Sales": d["revenue"]} for d in data])
        )
        ai_summary = generate_demand_summary(region_data=regional_summary, top_product="Overall")
        ai_recommendation = generate_recommendation(region_data=regional_summary, trending_products="Top Products")
    except Exception:
        ai_summary = "AI summary unavailable."
        ai_recommendation = "Recommendations unavailable."

    # Low-stock / reorder suggestion placeholder
    low_stock_products = (
        Product.query.filter(Product.shop_id == shop_id)
        .order_by(Product.price.asc())
        .limit(5)
        .all()
    )
    reorder_suggestions = [
        {
            "name": p.name,
            "price": f"₹{p.price:.0f}",
            "image": p.image_url or "https://placehold.co/400x300?text=Product",
            "category": p.category or "General",
            "rating": round(p.rating or 4.0, 1)
        }
        for p in low_stock_products
    ]

    ai_insights = [
        {"icon": "bi bi-lightbulb-fill", "title": "AI Demand Summary", "description": ai_summary},
        {"icon": "bi bi-bar-chart-fill", "title": "AI Recommendations", "description": ai_recommendation}
    ]

    return {
        "weekly_sales": f"₹{total_sales:,.0f}",
        "pending_reorders": len(reorder_suggestions),
        "total_orders": total_orders,
        "customer_rating": round(shop.rating or 4.0, 1),
        "weekly_summary": {
            "summary": ai_summary[:100] + "...",
            "avg_order_value": f"₹{avg_order_value:,.0f}"
        },
        "trend_chart": weekly_summary,
        "ai_insights": ai_insights,
        "reorder_suggestions": reorder_suggestions
    }


# Upload Sales Data (CSV)
def upload_sales_data(file, shop_id):
    """Parse and insert sales records from uploaded CSV."""
    try:
        df = pd.read_csv(file)
        required_cols = {"Date", "Region", "Product", "Quantity", "Revenue"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"CSV must contain columns: {required_cols}")

        records_added = []

        for _, row in df.iterrows():
            product = Product.query.filter(
                Product.name.ilike(f"%{row.get('Product', '')}%"),
                Product.shop_id == shop_id
            ).first()

            sale = SalesData(
                date=pd.to_datetime(row["Date"]).date(),
                region=row.get("Region", "Unknown"),
                product_id=product.id if product else None,
                shop_id=shop_id,
                quantity_sold=int(row["Quantity"]),
                revenue=float(row["Revenue"])
            )
            db.session.add(sale)
            records_added.append({
                "product": row.get("Product"),
                "quantity": int(row["Quantity"]),
                "revenue": float(row["Revenue"])
            })

        db.session.commit()
        return records_added

    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to upload sales data: {e}")


# ───────────────────────────────────────────────
# Export Sales Report (Excel)
# ───────────────────────────────────────────────
def export_sales_report(shop_id):
    """Generate Excel export for shop sales data."""
    shop = Shop.query.get(shop_id)
    if not shop:
        raise ValueError("Shop not found.")

    sales = (
        db.session.query(SalesData, Product)
        .join(Product, SalesData.product_id == Product.id)
        .filter(Product.shop_id == shop_id)
        .all()
    )

    if not sales:
        raise ValueError("No sales found for this shop.")

    data = [
        {
            "Date": s.date.strftime("%Y-%m-%d"),
            "Region": s.region,
            "Product": p.name if p else "N/A",
            "Quantity Sold": s.quantity_sold,
            "Revenue": f"₹{s.revenue:,.0f}"
        }
        for s, p in sales
    ]

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"sales_report_{datetime.utcnow().strftime('%Y%m%d')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
