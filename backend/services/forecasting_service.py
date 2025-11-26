# backend/services/forecasting_service.py

import pandas as pd
from services.prophet_service import prophet_manager

# -------------------- FORECAST SALES --------------------
def forecast_sales(df: pd.DataFrame):
    """
    Run optimized Prophet forecast and return next 4 weeks demand by product.
    Expects columns: 'Date', 'Sales', 'Product'
    """
    results = []

    if df.empty or not {'Date', 'Sales', 'Product'}.issubset(df.columns):
        print("[Warning] Invalid or empty DataFrame for forecast_sales.")
        return results

    for product in df['Product'].dropna().unique():
        product_df = df[df['Product'] == product][['Date', 'Sales']].copy()
        
        # Skip if insufficient data
        if len(product_df) < 5:
            print(f"[Warning] Not enough data for product '{product}' to forecast.")
            continue

        try:
            # Prepare data for optimized Prophet
            prophet_df = product_df.copy()
            prophet_df.columns = ["ds", "y"]  # Prophet expects ds, y columns
            
            # Use optimized Prophet service with 4 weeks forecast
            forecast_data, metrics = prophet_manager.forecast_sales(
                prophet_df, periods=4, freq='W'
            )
            
            # Convert to expected format
            forecast_list = []
            for _, row in forecast_data.iterrows():
                forecast_list.append({
                    "week": row['ds'].strftime('%Y-%m-%d'),
                    "predicted_sales": round(row['yhat'], 2)
                })

            results.append({
                "product": product,
                "forecast": forecast_list,
                "metrics": {
                    "data_quality_score": metrics.get('data_quality_score', 0),
                    "forecast_time_seconds": metrics.get('forecast_time_seconds', 0),
                    "model_cached": metrics.get('model_cached', False)
                }
            })
            
            print(f"[Success] Forecast for {product}: {metrics.get('forecast_time_seconds', 0):.2f}s")
            
        except Exception as e:
            print(f"[Error] Forecast error for {product}: {e}")

    return results


# -------------------- REGIONAL SUMMARY --------------------
def compute_regional_summary(df: pd.DataFrame):
    """
    Aggregate sales and compute share percentage per region.
    Expects columns: 'Region', 'Sales'
    """
    if df.empty or not {'Region', 'Sales'}.issubset(df.columns):
        print("[Warning] Invalid or empty DataFrame for compute_regional_summary.")
        return []

    try:
        region_summary = (
            df.groupby('Region', as_index=False)['Sales']
              .sum()
              .sort_values(by='Sales', ascending=False)
        )

        total_sales = region_summary['Sales'].sum()
        region_summary['Share (%)'] = (region_summary['Sales'] / total_sales * 100).round(1)

        return region_summary.to_dict(orient='records')
    except Exception as e:
        print(f"[Error] Regional Summary Error: {e}")
        return []


# -------------------- TOP TRENDING PRODUCTS --------------------
def top_trending_products(df: pd.DataFrame, top_n=5):
    """
    Identify top trending products with Month-over-Month (MoM) growth.
    Expects columns: 'Date', 'Product', 'Sales'
    """
    if df.empty or not {'Date', 'Product', 'Sales'}.issubset(df.columns):
        print("[Warning] Invalid or empty DataFrame for top_trending_products.")
        return []

    try:
        df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
        monthly = df.groupby(['Month', 'Product'], as_index=False)['Sales'].sum()

        if len(monthly['Month'].unique()) < 2:
            print("[Warning] Not enough months of data to compute MoM growth.")
            return []

        current_month = monthly['Month'].max()
        prev_month = current_month - 1

        current_sales = monthly[monthly['Month'] == current_month]
        prev_sales = monthly[monthly['Month'] == prev_month]

        merged = pd.merge(current_sales, prev_sales, on='Product', suffixes=('_curr', '_prev'))
        merged['Growth (%)'] = ((merged['Sales_curr'] - merged['Sales_prev']) / merged['Sales_prev'] * 100).round(1)

        top_products = merged.nlargest(top_n, 'Growth (%)')[['Product', 'Growth (%)', 'Sales_curr']]
        top_products.rename(columns={'Sales_curr': 'CurrentMonthSales'}, inplace=True)

        return top_products.to_dict(orient='records')
    except Exception as e:
        print(f"Top Trending Products Error: {e}")
        return []
