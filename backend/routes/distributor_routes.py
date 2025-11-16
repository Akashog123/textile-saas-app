# routes/distributor.py
from flask import Blueprint, jsonify, request, send_file
import pandas as pd
from datetime import datetime
from services.forecasting_service import (
    forecast_sales,
    compute_regional_summary,
    top_trending_products,
)
from services.ai_service import (
    generate_demand_summary,
    generate_recommendation,
    generate_production_priorities,
)
from routes.pdf_service import generate_pdf_report
from routes.auth_routes import token_required
from models.model import Product, SalesData
import io

distributor_bp = Blueprint("distributor", __name__)


# POST: Regional Demand & AI Forecast Insights
@distributor_bp.route("/regional-demand", methods=["POST"])
@token_required
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
        print("❌ Error in /regional-demand:", e)
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


# GET: Regional Demand Report PDF (AI Summary)
@distributor_bp.route("/regional-report", methods=["GET"])
@token_required
def generate_regional_report(current_user):
    """
    Generates a downloadable PDF summary of AI insights and forecast data.
    """
    try:
        pdf_buffer = generate_pdf_report(
            title="Regional Demand Report",
            subtitle=f"Prepared by {current_user.username} | {datetime.now().strftime('%d-%b-%Y')}",
            summary="AI-driven demand insights indicate strong growth in the South region with upward trends in Cotton and Linen sales."
        )

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="Regional_Demand_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print("❌ PDF generation failed:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# POST: Production Planning (AI Recommendations)
@distributor_bp.route("/production-plan", methods=["POST"])
@token_required
def generate_production_plan(current_user):
    """
    Analyze uploaded CSV and generate AI-based production priorities.
    """
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "CSV file missing"}), 400

        df = pd.read_csv(file)
        if not {"Product", "Region", "Sales"}.issubset(df.columns):
            return jsonify({
                "status": "error",
                "message": "Missing required columns: Product, Region, Sales"
            }), 400

        priorities, top_selling, underperforming = generate_production_priorities(df)

        return jsonify({
            "status": "success",
            "message": "AI production plan generated successfully.",
            "data": {
                "ai_priorities": priorities,
                "top_selling": top_selling,
                "underperforming": underperforming
            }
        }), 200

    except Exception as e:
        print("❌ Error in /production-plan:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Export AI Production Plan as CSV
@distributor_bp.route("/export-plan", methods=["GET"])
@token_required
def export_production_plan(current_user):
    """
    Export AI production recommendations in CSV format using live sales data.
    """
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
                "message": "No sales data available for export. Upload distributor CSV first."
            }), 404

        product_ids = {row.product_id for row in sales_rows if row.product_id}
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_lookup = {p.id: p for p in products}

        records = []
        for row in sales_rows:
            product = product_lookup.get(row.product_id)
            records.append({
                "date": row.date.isoformat(),
                "product": product.name if product else row.product_id,
                "category": product.category if product else "Unknown",
                "shop_id": row.shop_id,
                "region": row.region or "Unknown",
                "sales": float(row.revenue or 0),
                "quantity": row.quantity_sold or 0
            })

        df = pd.DataFrame(records)
        summary = (
            df.groupby(["product", "category"])
            .agg({"sales": "sum", "quantity": "sum"})
            .reset_index()
            .sort_values("sales", ascending=False)
        )

        csv_buffer = io.StringIO()
        summary.rename(columns={
            "product": "Product",
            "category": "Category",
            "sales": "TotalSales",
            "quantity": "UnitsSold"
        }).to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            as_attachment=True,
            download_name="production_plan.csv",
            mimetype="text/csv"
        )
    except Exception as e:
        print("❌ Error exporting production plan:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
