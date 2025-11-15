from flask import Blueprint, jsonify
from models.model import ExternalSalesDataItem, StoreRegion
from models.model import db
import pandas as pd
import numpy as np

heatmap_bp = Blueprint("heatmap", __name__, url_prefix="/region-demand-heatmap")

@heatmap_bp.route('/', methods=['GET'])
def region_demand_heatmap():
    """
    As a distributor, visualize which regions have rising or falling fabric demand
    using a JSON-based heatmap API.

    Output:
    [
        {
            "RegionName": "...",
            "Latitude": ...,
            "Longitude": ...,
            "Month": "January 2024",
            "UnitsSold": 1234,
            "DemandTrend": "Upward / Downward / Stable",
            "HeatmapScore": 0.83
        }
    ]
    """

    try:
        # STEP 1 — Join Region + Sales Data
        data = (
            db.session.query(
                StoreRegion.RegionName,
                StoreRegion.Latitude,
                StoreRegion.Longitude,
                ExternalSalesDataItem.UnitsSold,
                ExternalSalesDataItem.SaleDate
            )
            .join(StoreRegion, ExternalSalesDataItem.Region == StoreRegion.RegionName)
            .all()
        )

        if not data:
            return jsonify({"error": "No demand/sales data found"}), 404

        # STEP 2 — Convert to DataFrame
        df = pd.DataFrame([{
            "RegionName": d.RegionName,
            "Latitude": d.Latitude,
            "Longitude": d.Longitude,
            "UnitsSold": d.UnitsSold,
            "SaleDate": d.SaleDate
        } for d in data])

        df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors='coerce')
        df["Month"] = df["SaleDate"].dt.strftime("%B %Y")

        # STEP 3 — Aggregate monthly sales per region
        grouped = (
            df.groupby(["RegionName", "Latitude", "Longitude", "Month"])
            .agg({"UnitsSold": "sum"})
            .reset_index()
        )

        # STEP 4 — Determine trend (Upward / Downward / Stable)
        region_trends = []

        for region in grouped["RegionName"].unique():
            r_df = grouped[grouped["RegionName"] == region].sort_values("Month")

            r_df["Prev"] = r_df["UnitsSold"].shift(1)
            r_df["Trend"] = r_df.apply(
                lambda x: (
                    "Upward" if pd.notnull(x["Prev"]) and x["UnitsSold"] > x["Prev"]
                    else "Downward" if pd.notnull(x["Prev"]) and x["UnitsSold"] < x["Prev"]
                    else "Stable"
                ),
                axis=1
            )

            region_trends.append(r_df)

        trend_df = pd.concat(region_trends)

        # STEP 5 — Normalize UnitsSold to 0–1 for heatmap
        min_val = trend_df["UnitsSold"].min()
        max_val = trend_df["UnitsSold"].max()
        trend_df["HeatmapScore"] = (trend_df["UnitsSold"] - min_val) / (max_val - min_val + 1e-9)

        # STEP 6 — Final JSON output
        json_output = trend_df.to_dict(orient="records")

        return jsonify({
            "status": "success",
            "points": json_output
        })

    except Exception as e:
        return jsonify({"error": f"Heatmap processing failed: {str(e)}"}), 500

