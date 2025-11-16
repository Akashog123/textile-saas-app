import os
import io

# routes/distributor.py
from flask import Blueprint, jsonify, request, send_file
import pandas as pd
from datetime import datetime
from prophet import Prophet
from google.generativeai import configure, GenerativeModel
from services.forecasting_service import (
    forecast_sales,
    compute_regional_summary,
    top_trending_products,
)
from services.ai_service import (
    generate_demand_summary,
    generate_recommendation,
)
from routes.pdf_service import generate_pdf_report
# from routes.auth_routes import token_required
from models.model import Product, SalesData

configure(api_key=os.getenv("GEMINI_API_KEY", ""))

distributor_bp = Blueprint("distributor", __name__)


# POST: Regional Demand & AI Forecast Insights
@distributor_bp.route("/regional-demand", methods=["POST"])
# @token_required
def get_regional_demand(current_user):
    """
    Generate AI-powered regional demand insights and sales forecasting.
    Combines Prophet forecasting and Gemini AI-generated business insights.
    """
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"status": "error", "message": "No input file provided"}), 400

        # Read CSV or XLSX dynamically
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "Unsupported file format"}), 400

        # Validate required columns
        required_columns = {"Region", "Product", "Date", "Sales"}
        if not required_columns.issubset(df.columns):
            return jsonify({
                "status": "error",
                "message": f"Missing required columns: {', '.join(required_columns - set(df.columns))}"
            }), 400

        # Data processing through forecasting services
        regional_data = compute_regional_summary(df)
        trending_products = top_trending_products(df)
        forecasts = forecast_sales(df)

        # AI Insights from Gemini
        top_product = trending_products[0]["Product"] if trending_products else "Fabric"
        ai_summary = generate_demand_summary(regional_data, top_product, engine="gemini")
        ai_recommendation = generate_recommendation(regional_data, trending_products, engine="gemini")

        insights = {
            "ai_summary": ai_summary,
            "ai_recommendation": ai_recommendation,
            "regional_share": regional_data,
            "top_products": trending_products,
            "forecast": forecasts,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "analyst": current_user.username
        }

        return jsonify({
            "status": "success",
            "message": "AI regional demand insights generated successfully.",
            "data": insights
        }), 200

    except Exception as e:
        print("Error in /regional-demand:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to generate regional demand insights.",
            "error": str(e)
        }), 500


# GET: Sample Input Format for Distributor CSV
@distributor_bp.route("/sample-format", methods=["GET"])
def get_sample_format():
    """
    Provide a downloadable example structure for distributor uploads.
    Helps ensure users upload valid data for forecasting.
    """
    try:
        sample_data = {
            "Region": ["North", "South", "East", "West"],
            "Product": ["Silk", "Cotton", "Linen", "Wool"],
            "Date": ["2025-10-01", "2025-10-08", "2025-10-15", "2025-10-22"],
            "Sales": [5000, 3000, 4000, 2000]
        }
        return jsonify({
            "status": "success",
            "sample_structure": sample_data,
            "instructions": "Ensure your uploaded CSV/XLSX contains Region, Product, Date, and Sales columns."
        }), 200
    except Exception as e:
        print("Error generating sample format:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# Gemini Helper: AI-Generated Production Insight
def _generate_production_ai_summary(df, forecast_df):
    """Generate structured AI-based production plan recommendations using Gemini."""
    try:
        top_products = (
            df.groupby("Product")
            .sum(numeric_only=True)
            .sort_values("Sales", ascending=False)
            .head(5)
        )
        underperformers = (
            df.groupby("Product")
            .sum(numeric_only=True)
            .sort_values("Sales", ascending=True)
            .head(5)
        )

        summary_prompt = f"""
        You are an AI production planner for a textile manufacturer.
        Based on the following data, suggest production priorities and reasons.

        Top Performing Products:
        {top_products.to_string(index=True)}

        Underperforming Products:
        {underperformers.to_string(index=True)}

        Forecast Trends:
        {forecast_df[['ds','yhat']].tail(5).to_string(index=False)}

        Give your structured recommendations as:
        1. List of 3 prioritized actions: increase, maintain, reduce
        2. One short justification (1 line each)
        3. A one-line summary for the overall production strategy.
        """

        model = GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(summary_prompt)

        return result.text.strip() if result and result.text else (
            "Increase silk and cotton; maintain linen; reduce wool production due to declining demand."
        )

    except Exception as exc:  # pragma: no cover - fallback messaging
        print("[AI Production Plan Error]", exc)
        return "Unable to generate AI insights currently."


# POST: Production Planning (embedded implementation)
@distributor_bp.route("/production-plan", methods=["POST"])
# @token_required
def distributor_production_plan():
    """Upload sales CSV and get AI-powered production planning insights."""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400

        filename = (file.filename or "").lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "File must be .csv or .xlsx"}), 400

        if df.empty:
            return jsonify({"status": "error", "message": "Uploaded file has no rows"}), 400

        required_cols = {"Date", "Product", "Sales"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            return jsonify({
                "status": "error",
                "message": f"File must contain columns: {', '.join(sorted(required_cols))}",
                "missing": sorted(missing)
            }), 400

        df["ds"] = pd.to_datetime(df["Date"], errors="coerce")
        df["y"] = pd.to_numeric(df["Sales"], errors="coerce")
        df.dropna(subset=["ds", "y"], inplace=True)

        if df.empty:
            return jsonify({"status": "error", "message": "No valid Date/Sales rows after parsing"}), 400

        model = Prophet()
        model.fit(df[["ds", "y"]])
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        ai_summary = _generate_production_ai_summary(df, forecast)

        top_products = (
            df.groupby("Product")["Sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )
        underperforming = (
            df.groupby("Product")["Sales"]
            .sum()
            .sort_values(ascending=True)
            .head(5)
            .reset_index()
        )

        ai_priorities = []
        for _, row in top_products.iterrows():
            ai_priorities.append({
                "title": f"Increase Production: {row['Product']}",
                "detail": f"High sales of ₹{row['Sales']:,}. Forecast predicts upward trend.",
                "level": "increase",
            })
        for _, row in underperforming.iterrows():
            ai_priorities.append({
                "title": f"Reduce Production: {row['Product']}",
                "detail": f"Low sales (₹{row['Sales']:,}). Consider seasonal adjustments.",
                "level": "reduce",
            })

        return jsonify({
            "status": "success",
            "ai_summary": ai_summary,
            "ai_priorities": ai_priorities[:5],
            "top_selling": [
                {
                    "name": row["Product"],
                    "growth": f"+{round((row['Sales'] / df['Sales'].mean()) * 10, 1)}% MoM",
                    "volume": f"{row['Sales']} meters",
                    "image": "https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9"
                } for _, row in top_products.iterrows()
            ],
            "underperforming": [
                {
                    "name": row["Product"],
                    "decline": f"-{round((1 - row['Sales'] / df['Sales'].mean()) * 10, 1)}%",
                    "volume": int(row["Sales"]),
                    "image": "https://images.unsplash.com/photo-1636545732552-a94515d1b4c0"
                } for _, row in underperforming.iterrows()
            ]
        }), 200

    except Exception as exc:
        print("[Error - Production Plan]", exc)
        return jsonify({
            "status": "error",
            "message": "Failed to generate production plan.",
            "error": str(exc)
        }), 500


# GET: Export Production Plan CSV (embedded implementation)
@distributor_bp.route("/export-plan", methods=["GET"])
# @token_required
def distributor_export_plan():
    """Export a production plan CSV derived from live sales data."""
    try:
        window_start = datetime.utcnow().date().replace(day=1)
        sales_rows = (
            SalesData.query
            .filter(SalesData.date >= window_start)
            .all()
        )

        if not sales_rows:
            return jsonify({
                "status": "error",
                "message": "No sales data available for export this month."
            }), 404

        product_ids = {row.product_id for row in sales_rows if row.product_id}
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_lookup = {p.id: p for p in products}

        rows = []
        for entry in sales_rows:
            product = product_lookup.get(entry.product_id)
            rows.append({
                "Product": product.name if product else f"Product #{entry.product_id}",
                "Category": product.category if product else "Unknown",
                "Region": entry.region or "Unknown",
                "Revenue": float(entry.revenue or 0),
                "UnitsSold": entry.quantity_sold or 0
            })

        df = pd.DataFrame(rows)
        summary = (
            df.groupby(["Product", "Category"])
            .agg({"Revenue": "sum", "UnitsSold": "sum"})
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )

        csv_buf = io.StringIO()
        summary.to_csv(csv_buf, index=False)
        csv_buf.seek(0)

        return send_file(
            io.BytesIO(csv_buf.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="production_plan.csv",
        )
    except Exception as exc:
        print("[Error - Export Plan]", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


# GET: Regional Demand Report PDF (AI Summary)
@distributor_bp.route("/regional-report", methods=["GET"])
# @token_required
def generate_regional_report(current_user):
    """
    Generates a downloadable PDF summary of AI insights and forecast data.
    """
    try:
        username = getattr(current_user, "username", None)
        if not username and isinstance(current_user, dict):
            username = current_user.get("username")

        pdf_buffer = generate_pdf_report(
            title="Regional Demand Report",
            subtitle=f"Prepared by {username} | {datetime.now().strftime('%d-%b-%Y')}",
            summary="AI-driven demand insights indicate strong growth in the South region with upward trends in Cotton and Linen sales."
        )

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="Regional_Demand_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print("PDF generation failed:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
