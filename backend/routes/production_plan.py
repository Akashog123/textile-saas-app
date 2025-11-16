# routes/production_plan.py

import os
import io
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from prophet import Prophet
from google.generativeai import configure, GenerativeModel
from routes.auth_routes import token_required
from models.model import Product, SalesData

production_bp = Blueprint("production", __name__)

# Load Gemini API key from environment
configure(api_key=os.getenv("GEMINI_API_KEY", ""))


# Gemini Helper: AI-Generated Production Insight

def generate_production_plan(df, forecast_df):
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

    except Exception as e:
        print("[AI Production Plan Error]", e)
        return "Unable to generate AI insights currently."



# POST: Generate AI Production Plan + Forecast (handled via distributor blueprint)
@production_bp.route("/production-plan", methods=["POST"])
def production_plan():  # pragma: no cover - retained for backward compatibility
    return jsonify({
        "status": "error",
        "message": "Endpoint deprecated. Use /api/v1/distributor/production-plan instead."
    }), 410


# GET: Export AI Production Plan as CSV (handled via distributor blueprint)
@production_bp.route("/export-plan", methods=["GET"])
def export_plan():  # pragma: no cover - retained for backward compatibility
    return jsonify({
        "status": "error",
        "message": "Endpoint deprecated. Use /api/v1/distributor/export-plan instead."
    }), 410
