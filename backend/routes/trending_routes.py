import os
import json
import re
from flask import Blueprint, jsonify
from models.model import ExternalSalesDataItem, StoreRegion
from models.model import db
import pandas as pd
import google.generativeai as genai

trending_shops_bp = Blueprint("trending", __name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
model = genai.GenerativeModel("gemini-2.5-flash")

@trending_shops_bp.route('/', methods=['GET'])
def trending_shops():
    """Return per-store trend data with optional AI insights."""
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

    if not recent_sales:
        return jsonify({
            "status": "success",
            "trend_data": [],
            "ai_analysis": {},
            "message": "No sales data available to build trends."
        }), 200

    df = pd.DataFrame([{
        "Store": s.Store,
        "Region": s.Region,
        "SaleDate": s.SaleDate,
        "UnitsSold": s.UnitsSold,
        "Sales": s.Sales,
        "City": s.City,
        "RegionName": s.RegionName
    } for s in recent_sales])

    if df.empty:
        return jsonify({
            "status": "success",
            "trend_data": [],
            "ai_analysis": {},
            "message": "Sales dataset was empty."
        }), 200

    df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors="coerce")
    df.dropna(subset=["SaleDate"], inplace=True)

    if df.empty:
        return jsonify({
            "status": "success",
            "trend_data": [],
            "ai_analysis": {},
            "message": "Sales dates were invalid."
        }), 200

    df["Month"] = df["SaleDate"].dt.strftime("%B %Y")

    trend_df = df.groupby(["Store", "City", "RegionName", "Month"]) \
                 .agg({"UnitsSold": "sum", "Sales": "sum"}) \
                 .reset_index()

    ai_json = {}
    if not trend_df.empty and os.getenv("GEMINI_API_KEY"):
        try:
            ai_text = model.generate_content(
                f"Analyze textile shop trends:\n{trend_df.head(50).to_string()}"
            ).text
            match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            ai_json = json.loads(match.group(0)) if match else {}
        except Exception as exc:
            print("[Trending Shops AI]", exc)
            ai_json = {}

    return jsonify({
        "status": "success",
        "trend_data": trend_df.to_dict(orient="records"),
        "ai_analysis": ai_json
    }), 200
