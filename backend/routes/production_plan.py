# routes/production_plan.py

import os
import io
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from services.prophet_service import prophet_manager
from services.ai_providers import get_provider
from routes.auth_routes import token_required
from models.model import Product, SalesData

production_bp = Blueprint("production", __name__)

# Global AI provider
ai_provider = None
try:
    ai_provider = get_provider()
    print(f"Production plan AI Provider initialized: {ai_provider.__class__.__name__}")
except Exception as e:
    print(f"Failed to initialize AI provider for production plan: {e}")
    ai_provider = None

# AI Helper: AI-Generated Production Insight

def generate_production_plan(df, forecast_df):
    """Generate structured AI-based production plan recommendations using configured AI provider."""
    if not ai_provider:
        return {"error": "AI provider not configured"}
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

        result = ai_provider.generate_text(summary_prompt)

        return result if result else (
            "Increase silk and cotton; maintain linen; reduce wool production due to declining demand."
        )

    except Exception as e:
        print(f"[AI Production Plan Error] {ai_provider.__class__.__name__} error:", e)
        return "Unable to generate AI insights currently."


# GET: Generate production plan from database data
@production_bp.route("/production-plan-db", methods=["GET"])
@token_required
def get_production_plan_db(current_user):
    """Generate AI production plan using database sales data"""
    try:
        # Get recent sales data from database
        window_start = datetime.utcnow().date().replace(day=1)
        sales_rows = (
            SalesData.query
            .filter(SalesData.date >= window_start)
            .all()
        )

        if not sales_rows:
            return jsonify({
                "status": "error",
                "message": "No sales data available for production planning"
            }), 404

        # Get product information
        product_ids = {row.product_id for row in sales_rows if row.product_id}
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_lookup = {p.id: p for p in products}

        # Convert to DataFrame
        rows = []
        for entry in sales_rows:
            product = product_lookup.get(entry.product_id)
            rows.append({
                "Product": product.name if product else f"Product #{entry.product_id}",
                "Category": product.category if product else "Unknown",
                "Region": entry.region or "Unknown",
                "Sales": float(entry.revenue or 0),
                "Quantity": entry.quantity_sold or 0,
                "Date": entry.date
            })

        df = pd.DataFrame(rows)
        
        if df.empty:
            return jsonify({
                "status": "error",
                "message": "No valid sales data found"
            }), 404

        # Generate forecast using optimized Prophet
        try:
            # Prepare data for optimized Prophet
            prophet_df = df.groupby('Date')['Sales'].sum().reset_index()
            prophet_df.columns = ['ds', 'y']
            
            # Use optimized Prophet service
            forecast_data, metrics = prophet_manager.forecast_sales(prophet_df, periods=30)
            
            # Convert forecast data to expected format
            forecast = pd.DataFrame({
                'ds': forecast_data['ds'],
                'yhat': forecast_data['yhat'],
                'yhat_lower': forecast_data['yhat_lower'],
                'yhat_upper': forecast_data['yhat_upper']
            })
            
            print(f"[Optimized Prophet] Production plan forecast generated in {metrics.get('forecast_time_seconds', 0):.2f}s with MAE: {metrics.get('mae', 0):.2f}")
            
            # Generate AI insights
            ai_insights = generate_production_plan(df, forecast)
            
            return jsonify({
                "status": "success",
                "message": "Production plan generated successfully",
                "data": {
                    "ai_insights": ai_insights,
                    "top_products": df.groupby('Product')['Sales'].sum().sort_values(ascending=False).head(5).to_dict(),
                    "forecast_summary": {
                        "next_30_days_total": float(forecast.tail(30)['yhat'].sum()),
                        "growth_trend": "increasing" if forecast.tail(30)['yhat'].mean() > forecast.head(30)['yhat'].mean() else "decreasing"
                    },
                    "forecast_metrics": {
                        "forecast_time_seconds": metrics.get('forecast_time_seconds', 0),
                        "mae": metrics.get('mae', 0),
                        "rmse": metrics.get('rmse', 0)
                    },
                    "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Forecasting failed: {str(e)}"
            }), 500

    except Exception as e:
        print(f"[Production Plan DB Error]", e)
        return jsonify({
            "status": "error",
            "message": "Failed to generate production plan from database"
        }), 500



# POST: Generate AI Production Plan from uploaded file
@production_bp.route("/production-plan", methods=["POST"])
@token_required
def production_plan_upload(current_user):
    """Generate AI production plan from uploaded CSV/Excel file"""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({
                "status": "error",
                "message": "No file uploaded"
            }), 400

        # Validate file
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                "status": "error",
                "message": f"File must be one of: {', '.join(allowed_extensions)}"
            }), 400

        # Read file based on extension
        if file_ext == '.csv':
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if df.empty:
            return jsonify({
                "status": "error",
                "message": "Uploaded file is empty"
            }), 400

        # Validate required columns
        required_cols = {"Product", "Sales", "Date"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            return jsonify({
                "status": "error",
                "message": f"Missing required columns: {', '.join(missing)}",
                "required": list(required_cols)
            }), 400

        # Process data
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
        df.dropna(subset=['Date', 'Sales'], inplace=True)

        if df.empty:
            return jsonify({
                "status": "error",
                "message": "No valid Date/Sales data after processing"
            }), 400

        # Generate forecast using optimized Prophet
        try:
            # Prepare data for optimized Prophet
            prophet_df = df.groupby('Date')['Sales'].sum().reset_index()
            prophet_df.columns = ['ds', 'y']
            
            # Use optimized Prophet service
            forecast_data, metrics = prophet_manager.forecast_sales(prophet_df, periods=30)
            
            # Convert forecast data to expected format
            forecast = pd.DataFrame({
                'ds': forecast_data['ds'],
                'yhat': forecast_data['yhat'],
                'yhat_lower': forecast_data['yhat_lower'],
                'yhat_upper': forecast_data['yhat_upper']
            })
            
            print(f"[Optimized Prophet] File upload forecast generated in {metrics.get('forecast_time_seconds', 0):.2f}s with MAE: {metrics.get('mae', 0):.2f}")
            
            # Generate AI insights
            ai_insights = generate_production_plan(df, forecast)
            
            return jsonify({
                "status": "success",
                "message": "Production plan generated successfully from uploaded file",
                "data": {
                    "ai_insights": ai_insights,
                    "top_products": df.groupby('Product')['Sales'].sum().sort_values(ascending=False).head(5).to_dict(),
                    "forecast_summary": {
                        "next_30_days_total": float(forecast.tail(30)['yhat'].sum()),
                        "growth_trend": "increasing" if forecast.tail(30)['yhat'].mean() > forecast.head(30)['yhat'].mean() else "decreasing"
                    },
                    "forecast_metrics": {
                        "forecast_time_seconds": metrics.get('forecast_time_seconds', 0),
                        "mae": metrics.get('mae', 0),
                        "rmse": metrics.get('rmse', 0)
                    },
                    "data_summary": {
                        "total_products": df['Product'].nunique(),
                        "date_range": f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}",
                        "total_sales": float(df['Sales'].sum())
                    },
                    "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Forecasting failed: {str(e)}"
            }), 500

    except Exception as e:
        print(f"[Production Plan Upload Error]", e)
        return jsonify({
            "status": "error",
            "message": "Failed to process uploaded file"
        }), 500


# GET: Export production plan as CSV
@production_bp.route("/export-plan", methods=["GET"])
@token_required
def export_production_plan(current_user):
    """Export production plan CSV from database data"""
    try:
        # Get recent sales data
        window_start = datetime.utcnow().date().replace(day=1)
        sales_rows = (
            SalesData.query
            .filter(SalesData.date >= window_start)
            .all()
        )

        if not sales_rows:
            return jsonify({
                "status": "error",
                "message": "No sales data available for export"
            }), 404

        # Get product information
        product_ids = {row.product_id for row in sales_rows if row.product_id}
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_lookup = {p.id: p for p in products}

        # Prepare data
        rows = []
        for entry in sales_rows:
            product = product_lookup.get(entry.product_id)
            rows.append({
                "Product": product.name if product else f"Product #{entry.product_id}",
                "Category": product.category if product else "Unknown",
                "Region": entry.region or "Unknown",
                "Revenue": float(entry.revenue or 0),
                "UnitsSold": entry.quantity_sold or 0,
                "Date": entry.date.strftime('%Y-%m-%d') if entry.date else "Unknown"
            })

        df = pd.DataFrame(rows)
        
        # Create summary for production planning
        summary = (
            df.groupby(["Product", "Category"])
            .agg({"Revenue": "sum", "UnitsSold": "sum"})
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )

        # Create CSV
        csv_buf = io.StringIO()
        summary.to_csv(csv_buf, index=False)
        csv_buf.seek(0)

        return send_file(
            io.BytesIO(csv_buf.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"production_plan_{datetime.utcnow().strftime('%Y%m%d')}.csv",
        )

    except Exception as e:
        print(f"[Export Production Plan Error]", e)
        return jsonify({
            "status": "error",
            "message": "Failed to export production plan"
        }), 500
