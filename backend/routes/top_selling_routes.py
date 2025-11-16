import os
from flask import Blueprint, jsonify
from models.model import ExternalProduct, ExternalSalesDataItem
from models.model import db
import pandas as pd
import google.generativeai as genai

top_selling_bp = Blueprint("top_selling", __name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
model = genai.GenerativeModel("gemini-2.5-flash")

@top_selling_bp.route('/', methods=['GET'])
def top_selling_products():
    """Return yearly sales summary for the top external products."""

    top_5_product_ids = [
        p.ProductID for p in ExternalProduct.query.order_by(ExternalProduct.ProductID).limit(5).all()
    ]

    if not top_5_product_ids:
        return jsonify({
            "status": "error",
            "message": "No products found in external catalog"
        }), 404

    sales_data = (
        db.session.query(
            ExternalSalesDataItem.ProductID,
            ExternalSalesDataItem.Region,
            ExternalSalesDataItem.SaleDate,
            ExternalSalesDataItem.UnitsSold,
            ExternalSalesDataItem.Sales,
            ExternalProduct.ProductCategory.label('ProductName')
        )
        .join(ExternalProduct, ExternalSalesDataItem.ProductID == ExternalProduct.ProductID)
        .filter(ExternalSalesDataItem.ProductID.in_(top_5_product_ids))
        .all()
    )

    if not sales_data:
        return jsonify({
            "status": "success",
            "summary_table": [],
            "ai_analysis": "No sales data available."
        }), 200

    df = pd.DataFrame([{
        "ProductID": s.ProductID,
        "Region": s.Region,
        "ProductName": s.ProductName,
        "UnitsSold": s.UnitsSold,
        "Revenue": s.Sales,
        "Date": s.SaleDate
    } for s in sales_data])

    if df.empty:
        return jsonify({
            "status": "success",
            "summary_table": [],
            "ai_analysis": "Sales dataset was empty."
        }), 200

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.dropna(subset=['Date'], inplace=True)

    if df.empty:
        return jsonify({
            "status": "success",
            "summary_table": [],
            "ai_analysis": "Sales dates were invalid."
        }), 200

    df['Year'] = df['Date'].dt.year

    summary_df = (
        df.groupby(['ProductID', 'Region', 'Year', 'ProductName'])
        .agg({'UnitsSold': 'sum', 'Revenue': 'sum'})
        .reset_index()
    )

    ai_output = ""
    if not summary_df.empty and os.getenv("GEMINI_API_KEY"):
        prompt = f"""
        Analyze yearly sales and provide insights.
        Data: {summary_df.to_json(orient="records")}
        """
        try:
            ai_output = model.generate_content(prompt).text.strip()
        except Exception as exc:
            print("[Top Selling AI]", exc)
            ai_output = "AI analysis unavailable."
    else:
        ai_output = "No summarized sales data to analyze."

    return jsonify({
        "status": "success",
        "summary_table": summary_df.to_dict(orient="records"),
        "ai_analysis": ai_output
    }), 200
