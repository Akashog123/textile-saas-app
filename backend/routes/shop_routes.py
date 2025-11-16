import os
import random
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file
from models.model import db, SalesData
from services.ai_service import (
    forecast_trends,
    generate_demand_summary,
    generate_recommendation,
    generate_production_priorities,
)
from config import Config

shop_bp = Blueprint("shop", __name__)
INSTANCE_FOLDER = Config.DATA_DIR


# GET: AI-POWERED SHOP DASHBOARD + AUTO NEXT-MONTH FORECAST
@shop_bp.route("/dashboard", methods=["GET"])
def shop_dashboard():
    """
    AI-powered shop dashboard
    - Reads uploaded monthly CSV
    - Generates analytics & AI insights
    - Creates next-month synthetic forecast automatically
    """
    shop_id = request.args.get("shop_id", type=int)
    if not shop_id:
        return jsonify({"status": "error", "message": "shop_id is required."}), 400

    sales_path = os.path.join(INSTANCE_FOLDER, f"sales_shop_{shop_id}.csv")

    if not os.path.exists(sales_path):
        return jsonify({
            "status": "success",
            "data": {
                "weekly_sales": "₹0",
                "pending_reorders": 0,
                "total_orders": 0,
                "customer_rating": 4.0,
                "trend_chart": [],
                "ai_insights": [],
                "forecast": [],
                "reorder_suggestions": [],
                "production_priorities": []
            }
        }), 200

    try:
        # Load & Clean Data
        df = pd.read_csv(sales_path)
        if "date" not in df.columns:
            return jsonify({"status": "error", "message": "Invalid sales file format."}), 400

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df.dropna(subset=["date"], inplace=True)
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
        avg_order_value = weekly_sales / total_orders if total_orders else 0

        # Weekly Trend Chart
        trend_chart = (
            last_7_days.groupby(last_7_days["date"].dt.day_name())["revenue"]
            .sum()
            .reset_index()
            .rename(columns={"date": "day", "revenue": "sales"})
            .to_dict(orient="records")
        )

        # Forecast & AI Insights
        df_forecast = df[["date", "revenue"]].rename(columns={"date": "Date", "revenue": "Sales"})
        forecast_data = forecast_trends(df_forecast)

        # Summarize by fabric or category
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

        # AI insights
        top_item = forecast[0].get("fabric_type", "Cotton") if forecast else "Cotton"
        ai_insights = [
            {
                "title": f"{top_item} sales up {abs(int(growth))}%",
                "impact": "Positive" if growth >= 0 else "Negative",
                "category": "Trend",
            },
            {
                "title": "Consider restocking top-selling fabrics",
                "impact": "Inventory",
                "category": "Action",
            },
            {
                "title": f"Customer satisfaction steady at {round(random.uniform(3.8, 4.5), 1)}★",
                "impact": "Stable",
                "category": "Sentiment",
            },
        ]

        # AI Demand Summary & Recommendations
        demand_summary = generate_demand_summary(
            region_data=df.groupby("region")["revenue"].sum().to_dict() if "region" in df.columns else {},
            top_product=forecast[0].get("fabric_type", "Cotton") if forecast else "Cotton",
        )
        recommendation = generate_recommendation(
            region_data=df.groupby("region")["revenue"].sum().to_dict() if "region" in df.columns else {},
            trending_products=df.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(5).to_dict(),
        )

        # AI Production Priorities
        prod_df = df.rename(columns={"product_name": "Product", "revenue": "Sales", "region": "Region"})
        production_priorities, top_selling, underperforming = generate_production_priorities(prod_df)

        # Reorder Suggestions
        reorder_suggestions = (
            df.groupby("product_name")["quantity_sold"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
            .to_dict(orient="records")
        )

        # Auto-Generate Next Month Synthetic Forecast
        last_date = df["date"].max()
        next_month = (last_date + pd.offsets.MonthBegin(1)).month
        next_year = (last_date + pd.offsets.MonthBegin(1)).year

        synthetic_rows = []
        for _, row in df.sample(min(len(df), 30)).iterrows():
            new_date = (row["date"] + pd.offsets.MonthBegin(1)).replace(month=next_month)
            synthetic_rows.append({
                "date": new_date.strftime("%Y-%m-%d"),
                "product_name": row["product_name"],
                "category": row.get("category", ""),
                "region": row.get("region", ""),
                "fabric_type": row.get("fabric_type", ""),
                "quantity_sold": round(row["quantity_sold"] * random.uniform(0.9, 1.2)),
                "revenue": round(row["revenue"] * random.uniform(0.9, 1.25)),
            })

        synthetic_df = pd.DataFrame(synthetic_rows)
        combined_df = pd.concat([df, synthetic_df], ignore_index=True)
        combined_df.to_csv(sales_path, index=False)

        print(f"[AUTO] Synthetic next-month forecast appended for shop {shop_id}")

        # Final Dashboard Data
        dashboard_data = {
            "weekly_sales": f"₹{int(weekly_sales):,}",
            "avg_order_value": f"₹{int(avg_order_value):,}",
            "pending_reorders": random.randint(2, 5),
            "total_orders": total_orders,
            "customer_rating": round(random.uniform(3.9, 4.6), 1),
            "growth": f"{growth:.1f}%",
            "trend_chart": trend_chart,
            "forecast": forecast,
            "ai_insights": ai_insights,
            "demand_summary": demand_summary,
            "recommendation": recommendation,
            "production_priorities": production_priorities,
            "reorder_suggestions": reorder_suggestions,
            "top_selling": top_selling,
            "underperforming": underperforming,
            "forecast_chart": forecast_data,
        }

        return jsonify({"status": "success", "data": dashboard_data}), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500


# Upload Sales CSV
@shop_bp.route("/upload_sales_data", methods=["POST"])
def upload_sales_data():
    try:
        shop_id = request.form.get("shop_id")
        file = request.files.get("file")
        if not shop_id or not file:
            return jsonify({"status": "error", "message": "Missing shop_id or file."}), 400

        save_path = os.path.join(INSTANCE_FOLDER, f"sales_shop_{shop_id}.csv")
        file.save(save_path)
        print(f"[UPLOAD] Sales file saved: {save_path}")
        return jsonify({"status": "success", "message": "Sales data uploaded successfully!"}), 200
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Export Sales Report
@shop_bp.route("/sales/export", methods=["GET"])
def export_sales():
    try:
        shop_id = request.args.get("shop_id", type=int)
        if not shop_id:
            return jsonify({"status": "error", "message": "shop_id is required."}), 400

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
