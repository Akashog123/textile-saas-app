from flask import Blueprint, jsonify
from models.model import ExternalProduct, ExternalSalesDataItem
from models.model import db
import pandas as pd
import google.generativeai as genai

top_selling_bp = Blueprint("top_selling", __name__, url_prefix="/top-selling-products")

genai.configure(api_key="AIzaSyB4124DMFesEd6NXYhzsk6BQBIuKgZmnog")
model = genai.GenerativeModel("gemini-2.5-flash")

@top_selling_bp.route('/', methods=['GET'])
def top_selling_products():

    top_5_product_ids = [p.ProductID for p in ExternalProduct.query.order_by(ExternalProduct.ProductID).limit(5).all()]

    if not top_5_product_ids:
        return jsonify({"error": "No products found"}), 404

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

    df = pd.DataFrame([{
        "ProductID": s.ProductID,
        "Region": s.Region,
        "ProductName": s.ProductName,
        "UnitsSold": s.UnitsSold,
        "Revenue": s.Sales,
        "Date": s.SaleDate
    } for s in sales_data])

    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year

    summary_df = df.groupby(['ProductID','Region','Year','ProductName']) \
                   .agg({'UnitsSold':'sum','Revenue':'sum'}) \
                   .reset_index()

    prompt = f"""
    Analyze yearly sales and provide insights.
    Data: {summary_df.to_json(orient="records")}
    """

    ai_output = model.generate_content(prompt).text.strip()

    return jsonify({
        "summary_table": summary_df.to_dict(orient="records"),
        "ai_analysis": ai_output
    })
