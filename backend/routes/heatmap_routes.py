from flask import Blueprint, jsonify
from models.model import ExternalSalesDataItem, StoreRegion
from models.model import db
import pandas as pd

heatmap_bp = Blueprint("heatmap", __name__)


@heatmap_bp.route('/', methods=['GET'])
def region_demand_heatmap():
    """Return regional demand heatmap points with basic trend analysis."""
    try:
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
            return jsonify({
                "status": "error",
                "message": "No demand/sales data found"
            }), 404

        df = pd.DataFrame([{
            "RegionName": d.RegionName,
            "Latitude": d.Latitude,
            "Longitude": d.Longitude,
            "UnitsSold": d.UnitsSold,
            "SaleDate": d.SaleDate
        } for d in data])

        df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors='coerce')
        df.dropna(subset=["SaleDate"], inplace=True)
        if df.empty:
            return jsonify({
                "status": "success",
                "points": [],
                "message": "Sales dates were invalid."
            }), 200

        df["Month"] = df["SaleDate"].dt.to_period('M').dt.to_timestamp()

        grouped = (
            df.groupby(["RegionName", "Latitude", "Longitude", "Month"], as_index=False)
            .agg({"UnitsSold": "sum"})
            .sort_values("Month")
        )

        if grouped.empty:
            return jsonify({
                "status": "success",
                "points": []
            }), 200

        grouped["Prev"] = grouped.groupby("RegionName")["UnitsSold"].shift(1)
        grouped["DemandTrend"] = grouped.apply(
            lambda row: (
                "Upward" if pd.notnull(row["Prev"]) and row["UnitsSold"] > row["Prev"]
                else "Downward" if pd.notnull(row["Prev"]) and row["UnitsSold"] < row["Prev"]
                else "Stable"
            ),
            axis=1
        )

        min_val = grouped["UnitsSold"].min()
        max_val = grouped["UnitsSold"].max()
        grouped["HeatmapScore"] = (
            (grouped["UnitsSold"] - min_val) / (max_val - min_val + 1e-9)
        )

        grouped["Month"] = grouped["Month"].dt.strftime("%B %Y")

        return jsonify({
            "status": "success",
            "points": grouped.drop(columns=["Prev"]).to_dict(orient="records")
        }), 200

    except Exception as e:
        print("[Heatmap Error]", e)
        return jsonify({
            "status": "error",
            "message": "Heatmap processing failed.",
            "error": str(e)
        }), 500

