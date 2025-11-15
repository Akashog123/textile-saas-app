from flask import Blueprint, jsonify
from models.model import ExternalSalesDataItem, StoreRegion
from models.model import db
import pandas as pd
import google.generativeai as genai
import json, re

trending_shops_bp = Blueprint("trending", __name__, url_prefix="/trending_shops_bp")

genai.configure(api_key="AIzaSyB4124DMFesEd6NXYhzsk6BQBIuKgZmnog")
model = genai.GenerativeModel("gemini-2.5-flash")

@trending_shops_bp.route('/', methods=['GET'])
def trending_shops():
    recent_sales = (
        db.session.query(
            ExternalSalesDataItem.Store,
            ExternalSalesDataItem.Region,
            ExternalSalesDataItem.SaleDate,
            ExternalSalesDataItem.UnitsSold,
            ExternalSalesDataItem.Sales,
            StoreRegion.StoreName,
            StoreRegion.City,
            StoreRegion.RegionName
        )
        .join(StoreRegion, ExternalSalesDataItem.Store == StoreRegion.StoreName)
        .all()
    )

    df = pd.DataFrame([{
        "Store": s.Store,
        "Region": s.Region,
        "SaleDate": s.SaleDate,
        "UnitsSold": s.UnitsSold,
        "Sales": s.Sales,
        "City": s.City,
        "RegionName": s.RegionName
    } for s in recent_sales])

    df["SaleDate"] = pd.to_datetime(df["SaleDate"])
    df["Month"] = df["SaleDate"].dt.strftime("%B %Y")

    trend_df = df.groupby(["Store","City","RegionName","Month"]) \
                 .agg({"UnitsSold":"sum","Sales":"sum"}) \
                 .reset_index()
    trend_df.shape[0]
    ai_text = model.generate_content(
        f"Analyze textile shop trends:\n{trend_df.head(50).to_string()}"
    ).text

    match = re.search(r'\{.*\}', ai_text, re.DOTALL)
    ai_json = json.loads(match.group(0)) if match else {}

    return jsonify({
        "trend_data": trend_df.to_dict(orient="records"),
        "ai_analysis": ai_json
    })
