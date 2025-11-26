import os
import json
import re
from flask import Blueprint, jsonify
from models.model import ExternalSalesDataItem, StoreRegion
from models.model import db
import pandas as pd
from services.ai_providers import get_provider

trending_shops_bp = Blueprint("trending", __name__)

# Global AI provider
ai_provider = None
try:
    ai_provider = get_provider()
    print(f"Trending routes AI Provider initialized: {ai_provider.__class__.__name__}")
except Exception as e:
    print(f"Failed to initialize AI provider for trending routes: {e}")
    ai_provider = None

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
    if not trend_df.empty and ai_provider:
        try:
            # ai_text = ai_provider.generate_text(
            #     f"Analyze textile shop trends:\n{trend_df.head(50).to_string()}"
            # )
            # match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            # ai_json = json.loads(match.group(0)) if match else {}

            ai_json = {}
            if not trend_df.empty and ai_provider:
                try:
                    prompt = f"""
                    You are a textile retail analyst.
                    Analyze the following sales trends and respond ONLY in valid JSON.

                    Format strictly like this:
                    {{
                    "summary": {{
                        "overall_trend": "",
                        "top_performing_city": "",
                        "lowest_performing_city": "",
                        "best_month_overall": "",
                        "weak_month_pattern": ""
                    }},
                    "key_insights": [],
                    "recommendations": []
                    }}

                    DATA:
                    {trend_df.to_string()}
                    """
                    ai_text = ai_provider.generate_text(prompt)

                    # Remove markdown formatting if AI wraps response in ```json
                    clean_text = re.sub(r"```json|```", "", ai_text).strip()

                    try:
                        parsed = json.loads(clean_text)

                        ai_json = {
                            "summary": parsed.get("summary", {
                                "overall_trend": "AI response not in valid JSON",
                                "top_performing_city": "",
                                "lowest_performing_city": "",
                                "best_month_overall": "",
                                "weak_month_pattern": ""
                            }),
                            "recommendations": parsed.get("recommendations", [])
                        }

                    except Exception:
                        ai_json = {
                            "summary": {
                                "overall_trend": "AI response not in valid JSON",
                                "top_performing_city": "",
                                "lowest_performing_city": "",
                                "best_month_overall": "",
                                "weak_month_pattern": ""
                            },
                            "recommendations": []
                        }
                except Exception as exc:
                    print(f"[Trending Shops AI] {ai_provider.__class__.__name__} error:", exc)
                    ai_json = {}

        except Exception as exc:
            print(f"[Trending Shops AI] {ai_provider.__class__.__name__} error:", exc)
            ai_json = {}

    return jsonify({
        "status": "success",
        "trend_data": trend_df.to_dict(orient="records"),
        "ai_analysis": ai_json
    }), 200
