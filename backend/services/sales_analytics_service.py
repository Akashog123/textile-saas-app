# backend/services/sales_analytics_service.py
"""
Robust Sales Analytics Service for Shop Dashboard
Provides comprehensive sales summaries, trend analysis, and demand forecasting.
Uses ONLY database records from shop owner's periodic sales data uploads.
Includes DB-backed caching for AI insights and forecasts to prevent redundant API calls.
"""

import pandas as pd
import numpy as np
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

from models.model import db, SalesData, Product, Shop, CachedAIInsight, CachedForecast
from services.prophet_service import prophet_manager

logger = logging.getLogger(__name__)


# ============================================================================
# Cache TTL Configuration
# ============================================================================
FORECAST_TTL_HOURS = 24  # Forecasts valid for 24 hours unless new data uploaded
INSIGHTS_TTL_HOURS = 24  # AI insights valid for 24 hours unless new data uploaded


# ============================================================================
# Query Cache for Sales Analytics
# ============================================================================
class SalesQueryCache:
    """Query cache DISABLED - always fetches fresh data from DB."""
    
    def __init__(self, ttl_seconds: int = 300):
        pass
    
    def _make_key(self, shop_id: int, method: str, *args) -> str:
        return ""
    
    def get(self, shop_id: int, method: str, *args) -> Optional[Any]:
        # Always return None - no caching, fetch fresh from DB
        return None
    
    def set(self, shop_id: int, method: str, value: Any, *args):
        # No-op - caching disabled
        pass
    
    def invalidate(self, shop_id: int):
        # No-op - caching disabled
        pass


# Global query cache instance
_query_cache = SalesQueryCache(ttl_seconds=300)


class SalesAnalyticsService:
    """
    Comprehensive sales analytics service using ONLY database records.
    Data comes from SalesData table populated by shop owner's periodic uploads.
    Includes query caching for better performance with repeated requests.
    Uses DB-backed caching for forecasts and AI insights to prevent redundant computations.
    """
    
    def __init__(self, shop_id: int):
        self.shop_id = shop_id
        self._cache = _query_cache
    
    # =========================================================================
    # DB-BACKED FORECAST CACHING
    # =========================================================================
    
    def _get_data_hash(self, days: int = 90) -> str:
        """Generate a hash of sales data to detect changes."""
        try:
            # Get count and latest date for quick hash
            from sqlalchemy import func
            result = db.session.query(
                func.count(SalesData.id),
                func.max(SalesData.date),
                func.sum(SalesData.revenue)
            ).filter(
                SalesData.shop_id == self.shop_id
            ).first()
            
            count, max_date, total_revenue = result if result else (0, None, 0)
            hash_input = f"{self.shop_id}:{count}:{max_date}:{total_revenue}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating data hash: {e}")
            return ""
    
    def _get_cached_forecast(self, forecast_type: str) -> Optional[Dict]:
        """
        Get cached forecast from database if still valid.
        Returns None if no valid cache exists or data has changed.
        """
        try:
            data_hash = self._get_data_hash()
            cached = CachedForecast.query.filter_by(
                shop_id=self.shop_id,
                forecast_type=forecast_type
            ).first()
            
            if cached:
                # Check if data hash matches (data hasn't changed)
                if cached.data_hash != data_hash:
                    logger.info(f"[Cache Miss] Data changed for shop {self.shop_id}")
                    return None
                
                # Check if cache is expired
                if cached.expires_at and datetime.utcnow() > cached.expires_at:
                    logger.info(f"[Cache Miss] Expired for shop {self.shop_id}")
                    return None
                
                logger.info(f"[Cache Hit] Using cached forecast for shop {self.shop_id}")
                return json.loads(cached.forecast_data) if isinstance(cached.forecast_data, str) else cached.forecast_data
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached forecast: {e}")
            return None
    
    def _save_cached_forecast(self, forecast_type: str, forecast_data: Dict):
        """Save forecast to database cache."""
        try:
            data_hash = self._get_data_hash()
            expires_at = datetime.utcnow() + timedelta(hours=FORECAST_TTL_HOURS)
            
            # Delete existing cache for this shop/type
            CachedForecast.query.filter_by(
                shop_id=self.shop_id,
                forecast_type=forecast_type
            ).delete()
            
            # Create new cache entry
            cached = CachedForecast(
                shop_id=self.shop_id,
                forecast_type=forecast_type,
                forecast_data=json.dumps(forecast_data) if not isinstance(forecast_data, str) else forecast_data,
                data_hash=data_hash,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )
            db.session.add(cached)
            db.session.commit()
            logger.info(f"[Cache Save] Saved forecast for shop {self.shop_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving cached forecast: {e}")
    
    def invalidate_forecasts(self):
        """Invalidate all cached forecasts for this shop."""
        try:
            CachedForecast.query.filter_by(shop_id=self.shop_id).delete()
            db.session.commit()
            logger.info(f"[Cache Invalidate] Cleared forecast cache for shop {self.shop_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error invalidating forecasts: {e}")
    
    # =========================================================================
    # DATA LOADING - Database Only
    # =========================================================================
    
    def _load_sales_data(self, days: int = 90) -> pd.DataFrame:
        """
        Load sales data ONLY from database SalesData table.
        This ensures we use only the shop owner's uploaded sales data.
        Uses caching to avoid repeated database queries.
        """
        try:
            # Check cache first
            cached = self._cache.get(self.shop_id, "_load_sales_data", days)
            if cached is not None:
                return cached
            
            cutoff_date = datetime.now().date() - timedelta(days=days)
            
            sales_records = SalesData.query.filter(
                SalesData.shop_id == self.shop_id,
                SalesData.date >= cutoff_date
            ).all()
            
            if not sales_records:
                logger.info(f"No sales data found in DB for shop {self.shop_id}")
                return pd.DataFrame()
            
            data = []
            for record in sales_records:
                # Get product details if available
                product_name = None
                category = record.fabric_type  # Default to fabric_type
                
                if record.product_id:
                    product = Product.query.get(record.product_id)
                    if product:
                        product_name = product.name
                        # Product uses 'category'
                        category = product.category or record.fabric_type
                
                data.append({
                    'date': record.date,
                    'product_id': record.product_id,
                    'product_name': product_name,
                    'region': record.region,
                    'category': category,
                    'quantity_sold': record.quantity_sold or 0,
                    'revenue': float(record.revenue or 0)
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            logger.info(f"Loaded {len(df)} sales records from DB for shop {self.shop_id}")
            
            # Cache the result
            self._cache.set(self.shop_id, "_load_sales_data", df, days)
            return df
            
        except Exception as e:
            logger.error(f"Error loading sales data for shop {self.shop_id}: {e}")
            return pd.DataFrame()
    
    def invalidate_cache(self):
        """Invalidate cache when new data is uploaded."""
        self._cache.invalidate(self.shop_id)
    
    def get_sales_data(self, days: int = 90) -> pd.DataFrame:
        """
        Get sales data for analysis. Uses only database records."""
        return self._load_sales_data(days)
    
    # =========================================================================
    # WEEKLY SALES SUMMARY (Last 7 Days)
    # =========================================================================
    
    def get_weekly_sales_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive weekly sales summary for last 7 days.
        Uses ONLY database records from shop owner's uploaded sales data.
        """
        df = self.get_sales_data(days=21)  # Get 3 weeks for comparison
        
        now = datetime.now()
        week_start = now - timedelta(days=7)
        prev_week_start = now - timedelta(days=14)
        
        default_response = {
            "status": "no_data",
            "period": {
                "start": week_start.strftime("%Y-%m-%d"),
                "end": now.strftime("%Y-%m-%d"),
                "label": "Last 7 Days"
            },
            "metrics": {
                "total_revenue": 0,
                "total_revenue_formatted": "₹0",
                "total_quantity": 0,
                "total_orders": 0,
                "average_order_value": 0,
                "average_order_value_formatted": "₹0"
            },
            "comparison": {
                "revenue_change": 0,
                "revenue_change_percent": "0%",
                "quantity_change": 0,
                "quantity_change_percent": "0%",
                "trend": "stable"
            },
            "daily_breakdown": [],
            "top_products": [],
            "top_categories": [],
            "insights": []
        }
        
        if df.empty:
            default_response["insights"] = [{
                "type": "info",
                "title": "No Sales Data",
                "message": "Upload your sales data to see weekly analytics and insights."
            }]
            return default_response
        
        # Current week data
        current_week = df[df['date'] >= week_start]
        prev_week = df[(df['date'] >= prev_week_start) & (df['date'] < week_start)]
        
        # Calculate metrics
        current_revenue = current_week['revenue'].sum()
        current_quantity = current_week['quantity_sold'].sum()
        current_orders = len(current_week)
        
        prev_revenue = prev_week['revenue'].sum()
        prev_quantity = prev_week['quantity_sold'].sum()
        
        # Calculate changes
        revenue_change = current_revenue - prev_revenue
        revenue_change_pct = (revenue_change / prev_revenue * 100) if prev_revenue > 0 else 0
        quantity_change = current_quantity - prev_quantity
        quantity_change_pct = (quantity_change / prev_quantity * 100) if prev_quantity > 0 else 0
        
        # Determine trend
        if revenue_change_pct > 5:
            trend = "up"
        elif revenue_change_pct < -5:
            trend = "down"
        else:
            trend = "stable"
        
        # Daily breakdown
        daily_data = current_week.groupby(current_week['date'].dt.date).agg({
            'revenue': 'sum',
            'quantity_sold': 'sum'
        }).reset_index()
        
        daily_breakdown = []
        for _, row in daily_data.iterrows():
            daily_breakdown.append({
                "date": row['date'].strftime("%Y-%m-%d"),
                "day_name": pd.Timestamp(row['date']).day_name(),
                "revenue": round(float(row['revenue']), 2),
                "revenue_formatted": f"₹{row['revenue']:,.0f}",
                "quantity": int(row['quantity_sold'])
            })
        
        # Top products (if product info available)
        top_products = []
        if 'product_name' in current_week.columns or 'product_id' in current_week.columns:
            product_col = 'product_name' if 'product_name' in current_week.columns else 'product_id'
            top_prods = current_week.groupby(product_col).agg({
                'revenue': 'sum',
                'quantity_sold': 'sum'
            }).sort_values('revenue', ascending=False).head(5)
            
            for name, row in top_prods.iterrows():
                top_products.append({
                    "name": str(name),
                    "revenue": round(float(row['revenue']), 2),
                    "quantity": int(row['quantity_sold'])
                })
                # Top categories
        top_categories = []
        category_col = 'category' if 'category' in current_week.columns else None
        
        # Fallback for legacy data with fabric_type
        if not category_col and 'fabric_type' in current_week.columns:
            category_col = 'fabric_type'
        
        if category_col:
            top_cats = current_week.groupby(category_col).agg({
                'revenue': 'sum',
                'quantity_sold': 'sum'
            }).sort_values('revenue', ascending=False).head(5)
            
            for name, row in top_cats.iterrows():
                if pd.notna(name):
                    top_categories.append({
                        "name": str(name),
                        "revenue": round(float(row['revenue']), 2),
                        "percentage": round(float(row['revenue']) / current_revenue * 100, 1) if current_revenue > 0 else 0
                    })
        
        # Generate insights (pass daily_breakdown and df for richer analysis)
        insights = self._generate_weekly_insights(
            current_revenue, prev_revenue, revenue_change_pct,
            current_quantity, prev_quantity, top_products, top_categories,
            daily_breakdown=daily_breakdown, df=current_week
        )
        
        avg_order_value = current_revenue / current_orders if current_orders > 0 else 0
        
        return {
            "status": "success",
            "period": {
                "start": week_start.strftime("%Y-%m-%d"),
                "end": now.strftime("%Y-%m-%d"),
                "label": "Last 7 Days"
            },
            "metrics": {
                "total_revenue": round(float(current_revenue), 2),
                "total_revenue_formatted": f"₹{current_revenue:,.0f}",
                "total_quantity": int(current_quantity),
                "total_orders": current_orders,
                "average_order_value": round(float(avg_order_value), 2),
                "average_order_value_formatted": f"₹{avg_order_value:,.0f}"
            },
            "comparison": {
                "revenue_change": round(float(revenue_change), 2),
                "revenue_change_percent": f"{revenue_change_pct:+.1f}%",
                "quantity_change": int(quantity_change),
                "quantity_change_percent": f"{quantity_change_pct:+.1f}%",
                "trend": trend,
                "previous_revenue": round(float(prev_revenue), 2),
                "previous_revenue_formatted": f"₹{prev_revenue:,.0f}"
            },
            "daily_breakdown": daily_breakdown,
            "top_products": top_products,
            "top_categories": top_categories,
            "insights": insights
        }
    
    def _generate_weekly_insights(
        self, current_revenue: float, prev_revenue: float, revenue_change_pct: float,
        current_qty: int, prev_qty: int, top_products: List, top_categories: List,
        daily_breakdown: List = None, df: pd.DataFrame = None
    ) -> List[Dict]:
        """Generate actionable, unique insights from weekly data"""
        insights = []
        
        # 1. Sales Velocity Insight - Calculate average daily sales rate
        if current_qty > 0:
            avg_daily_units = current_qty / 7
            if avg_daily_units >= 30:
                velocity_status = "high"
                velocity_msg = f"You're selling {avg_daily_units:.0f} units/day on average. Strong velocity!"
            elif avg_daily_units >= 10:
                velocity_status = "good"
                velocity_msg = f"Steady pace at {avg_daily_units:.0f} units/day. Room to push harder."
            else:
                velocity_status = "slow"
                velocity_msg = f"Only {avg_daily_units:.1f} units/day. Consider flash sales or bundles."
            
            insights.append({
                "type": "success" if velocity_status == "high" else "info" if velocity_status == "good" else "warning",
                "icon": "bi-speedometer2",
                "title": "Sales Velocity",
                "message": velocity_msg,
                "category": "Performance"
            })
        
        # 2. Best Selling Day Analysis
        if daily_breakdown and len(daily_breakdown) > 0:
            best_day = max(daily_breakdown, key=lambda x: x.get('revenue', 0))
            worst_day = min(daily_breakdown, key=lambda x: x.get('revenue', 0))
            
            if best_day.get('revenue', 0) > 0:
                insights.append({
                    "type": "success",
                    "icon": "bi-calendar-check",
                    "title": "Peak Sales Day",
                    "message": f"{best_day.get('day_name', 'N/A')} was your best day with {best_day.get('revenue_formatted', '₹0')}. Plan promotions around this day!",
                    "category": "Timing"
                })
            
            # Only show worst day insight if there's meaningful difference
            if best_day.get('revenue', 0) > 0 and worst_day.get('revenue', 0) >= 0:
                diff_pct = ((best_day.get('revenue', 0) - worst_day.get('revenue', 1)) / best_day.get('revenue', 1)) * 100 if best_day.get('revenue', 0) > 0 else 0
                if diff_pct > 50:
                    insights.append({
                        "type": "warning",
                        "icon": "bi-calendar-x",
                        "title": "Opportunity Day",
                        "message": f"{worst_day.get('day_name', 'N/A')} had {diff_pct:.0f}% less sales. Run {worst_day.get('day_name', '')} specials!",
                        "category": "Timing"
                    })
        
        # 3. Revenue per Unit (Pricing Power)
        if current_qty > 0 and current_revenue > 0:
            avg_price = current_revenue / current_qty
            prev_avg_price = prev_revenue / prev_qty if prev_qty > 0 else 0
            price_change = ((avg_price - prev_avg_price) / prev_avg_price * 100) if prev_avg_price > 0 else 0
            
            if price_change > 10:
                insights.append({
                    "type": "success",
                    "icon": "bi-cash-stack",
                    "title": "Pricing Power Up",
                    "message": f"Avg. revenue per item is ₹{avg_price:,.0f} (+{price_change:.0f}% vs last week). Premium products are selling!",
                    "category": "Pricing"
                })
            elif price_change < -10:
                insights.append({
                    "type": "warning",
                    "icon": "bi-tag",
                    "title": "Price Pressure",
                    "message": f"Avg. revenue per item dropped to ₹{avg_price:,.0f}. Review discounting strategy.",
                    "category": "Pricing"
                })
        
        # 4. Category Concentration Risk
        if top_categories and len(top_categories) > 0:
            top_cat = top_categories[0]
            if top_cat['percentage'] > 60:
                insights.append({
                    "type": "warning",
                    "icon": "bi-exclamation-triangle",
                    "title": "Category Concentration",
                    "message": f"{top_cat['name']} dominates at {top_cat['percentage']:.0f}% of sales. Diversify to reduce risk.",
                    "category": "Strategy"
                })
            elif len(top_categories) >= 3 and all(cat['percentage'] >= 15 for cat in top_categories[:3]):
                insights.append({
                    "type": "success",
                    "icon": "bi-pie-chart",
                    "title": "Healthy Category Mix",
                    "message": "Revenue well-distributed across categories. Great portfolio balance!",
                    "category": "Strategy"
                })
        
        # 5. Growth Momentum Analysis
        if prev_revenue > 0:
            if revenue_change_pct > 20:
                insights.append({
                    "type": "success",
                    "icon": "bi-rocket-takeoff",
                    "title": "Momentum Building",
                    "message": f"+{revenue_change_pct:.1f}% growth! Capitalize with expanded inventory & marketing.",
                    "category": "Trend"
                })
            elif revenue_change_pct < -20:
                insights.append({
                    "type": "warning",
                    "icon": "bi-arrow-down-circle",
                    "title": "Action Required",
                    "message": f"Revenue down {abs(revenue_change_pct):.1f}%. Consider clearance sales or new product launches.",
                    "category": "Trend"
                })
        
        # 6. Top Product Growth Potential
        if top_products and len(top_products) >= 2:
            top_prod = top_products[0]
            second_prod = top_products[1]
            gap = top_prod['revenue'] - second_prod['revenue']
            
            if gap > top_prod['revenue'] * 0.5:
                insights.append({
                    "type": "info",
                    "icon": "bi-star",
                    "title": "Hero Product",
                    "message": f"'{top_prod['name'][:25]}...' leads by ₹{gap:,.0f}. Stock up & feature prominently!",
                    "category": "Product"
                })
            else:
                insights.append({
                    "type": "info",
                    "icon": "bi-trophy",
                    "title": "Competitive Top Products",
                    "message": f"Top 2 products neck-to-neck. Cross-promote as bundle for higher AOV.",
                    "category": "Product"
                })
        
        # 7. Quantity vs Revenue Insight
        qty_change_pct = ((current_qty - prev_qty) / prev_qty * 100) if prev_qty > 0 else 0
        if current_qty > 0 and prev_qty > 0:
            if qty_change_pct > 0 and revenue_change_pct < 0:
                insights.append({
                    "type": "warning",
                    "icon": "bi-currency-exchange",
                    "title": "Margin Alert",
                    "message": f"Units up {qty_change_pct:.0f}% but revenue down. Check if discounts are too deep.",
                    "category": "Pricing"
                })
            elif qty_change_pct < 0 and revenue_change_pct > 0:
                insights.append({
                    "type": "success",
                    "icon": "bi-gem",
                    "title": "Premium Shift",
                    "message": f"Fewer units, higher revenue! Customers choosing premium products.",
                    "category": "Product"
                })
        
        # Limit to top 5 most actionable insights
        return insights[:5]
    
    # =========================================================================
    # SALES GROWTH TREND (Weekly/Monthly/Yearly)
    # =========================================================================
    
    def get_sales_growth_trend(self, period: str = 'weekly') -> Dict[str, Any]:
        """
        Get sales growth trend data for charting.
        
        Args:
            period: 'weekly' (last 7 days), 'monthly' (last 30 days), 'yearly' (last 12 months)
        
        Returns:
            Chart data with labels, values, and growth metrics
        """
        now = datetime.now()
        
        # Determine date range and aggregation based on period
        if period == 'weekly':
            days = 7
            df = self.get_sales_data(days=14)  # Get 2 weeks for comparison
            date_format = '%a'  # Mon, Tue, etc.
        elif period == 'monthly':
            days = 30
            df = self.get_sales_data(days=60)  # Get 2 months for comparison
            date_format = '%d %b'  # 01 Dec, 02 Dec, etc.
        else:  # yearly
            days = 365
            df = self.get_sales_data(days=730)  # Get 2 years for comparison
            date_format = '%b %Y'  # Jan 2025, Feb 2025, etc.
        
        default_response = {
            "status": "no_data",
            "period": period,
            "labels": [],
            "data": [],
            "chart_path": "",
            "total_revenue": 0,
            "total_revenue_formatted": "₹0",
            "growth_percent": 0,
            "growth_percent_formatted": "0%",
            "trend": "stable",
            "data_points": []
        }
        
        if df.empty:
            # Return empty chart data with appropriate labels
            if period == 'weekly':
                default_response["labels"] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                default_response["data"] = [0] * 7
            elif period == 'monthly':
                default_response["labels"] = [(now - timedelta(days=i)).strftime('%d') for i in range(29, -1, -1)]
                default_response["data"] = [0] * 30
            else:
                default_response["labels"] = [(now - timedelta(days=i*30)).strftime('%b') for i in range(11, -1, -1)]
                default_response["data"] = [0] * 12
            return default_response
        
        # Current period data
        current_start = now - timedelta(days=days)
        current_df = df[df['date'] >= current_start]
        
        # Previous period data for comparison
        prev_start = current_start - timedelta(days=days)
        prev_df = df[(df['date'] >= prev_start) & (df['date'] < current_start)]
        
        # Aggregate by time period
        if period == 'yearly':
            # Group by month for yearly view
            current_df = current_df.copy()
            current_df['period'] = current_df['date'].dt.to_period('M')
            aggregated = current_df.groupby('period').agg({
                'revenue': 'sum',
                'quantity_sold': 'sum'
            }).reset_index()
            aggregated['date'] = aggregated['period'].dt.to_timestamp()
            aggregated = aggregated.sort_values('date')
            
            # Fill missing months
            all_months = pd.date_range(start=current_start, end=now, freq='MS')
            month_data = []
            for month in all_months:
                month_period = month.to_period('M')
                match = aggregated[aggregated['period'] == month_period]
                if not match.empty:
                    month_data.append({
                        'label': month.strftime('%b'),
                        'revenue': float(match['revenue'].iloc[0]),
                        'quantity': int(match['quantity_sold'].iloc[0])
                    })
                else:
                    month_data.append({
                        'label': month.strftime('%b'),
                        'revenue': 0,
                        'quantity': 0
                    })
            
            labels = [d['label'] for d in month_data]
            data = [d['revenue'] for d in month_data]
            
        else:
            # Group by day for weekly/monthly view
            current_df = current_df.copy()
            current_df['day'] = current_df['date'].dt.date
            daily = current_df.groupby('day').agg({
                'revenue': 'sum',
                'quantity_sold': 'sum'
            }).reset_index()
            
            # Fill missing days
            all_days = pd.date_range(start=current_start, end=now, freq='D')
            day_data = []
            for day in all_days:
                day_date = day.date()
                match = daily[daily['day'] == day_date]
                if not match.empty:
                    day_data.append({
                        'label': day.strftime(date_format),
                        'date': day_date.isoformat(),
                        'revenue': float(match['revenue'].iloc[0]),
                        'quantity': int(match['quantity_sold'].iloc[0])
                    })
                else:
                    day_data.append({
                        'label': day.strftime(date_format),
                        'date': day_date.isoformat(),
                        'revenue': 0,
                        'quantity': 0
                    })
            
            # For weekly, only take last 7 days
            if period == 'weekly':
                day_data = day_data[-7:]
            
            labels = [d['label'] for d in day_data]
            data = [d['revenue'] for d in day_data]
        
        # Calculate totals and growth
        current_total = sum(data)
        prev_total = prev_df['revenue'].sum() if not prev_df.empty else 0
        
        if prev_total > 0:
            growth_percent = ((current_total - prev_total) / prev_total) * 100
        elif current_total > 0:
            growth_percent = 100
        else:
            growth_percent = 0
        
        # Determine trend
        if growth_percent > 5:
            trend = "up"
        elif growth_percent < -5:
            trend = "down"
        else:
            trend = "stable"
        
        # Generate SVG path for chart
        chart_path, chart_area_path = self._generate_svg_paths(data)
        
        # Create data points for interactive chart
        data_points = []
        max_val = max(data) if data and max(data) > 0 else 1
        for i, (label, value) in enumerate(zip(labels, data)):
            x = (i / max(len(data) - 1, 1)) * 400
            y = 160 - ((value / max_val) * 130) if max_val > 0 else 160
            data_points.append({
                'x': round(x, 1),
                'y': round(max(30, min(160, y)), 1),
                'value': round(value, 2),
                'value_formatted': f"₹{value:,.0f}",
                'label': label
            })
        
        return {
            "status": "success",
            "period": period,
            "labels": labels,
            "data": data,
            "chart_path": chart_path,
            "chart_area_path": chart_area_path,
            "total_revenue": round(current_total, 2),
            "total_revenue_formatted": f"₹{current_total:,.0f}",
            "growth_percent": round(growth_percent, 1),
            "growth_percent_formatted": f"{growth_percent:+.1f}%",
            "trend": trend,
            "data_points": data_points,
            "comparison": {
                "current_total": round(current_total, 2),
                "previous_total": round(prev_total, 2),
                "difference": round(current_total - prev_total, 2)
            }
        }
    
    def _generate_svg_paths(self, data: List[float]) -> tuple:
        """Generate SVG path strings for the chart line and area fill"""
        if not data or all(v == 0 for v in data):
            # Return flat line at bottom
            return "M0,160 L400,160", "M0,160 L400,160 L400,180 L0,180 Z"
        
        max_val = max(data) if max(data) > 0 else 1
        points = []
        
        for i, value in enumerate(data):
            x = (i / max(len(data) - 1, 1)) * 400
            y = 160 - ((value / max_val) * 130)
            y = max(30, min(160, y))
            points.append((round(x, 1), round(y, 1)))
        
        # Generate line path
        path_parts = [f"M{points[0][0]},{points[0][1]}"]
        for x, y in points[1:]:
            path_parts.append(f"L{x},{y}")
        line_path = " ".join(path_parts)
        
        # Generate area path (closed for gradient fill)
        area_path = line_path + f" L400,180 L0,180 Z"
        
        return line_path, area_path
    
    # =========================================================================
    # QUARTERLY DEMAND FORECAST
    # =========================================================================
    
    def get_quarterly_demand_forecast(self) -> Dict[str, Any]:
        """
        Generate next quarter (90 days) demand forecast using Prophet.
        Uses DB caching to avoid redundant Prophet computations.
        Returns weekly predictions with confidence intervals.
        """
        # Check DB cache first
        cached_forecast = self._get_cached_forecast('quarterly')
        if cached_forecast:
            return cached_forecast
        
        df = self.get_sales_data(days=365)  # Use up to 1 year of data from DB
        
        now = datetime.now()
        quarter_end = now + timedelta(days=90)
        
        default_response = {
            "status": "no_data",
            "forecast_period": {
                "start": now.strftime("%Y-%m-%d"),
                "end": quarter_end.strftime("%Y-%m-%d"),
                "label": "Next Quarter (90 Days)"
            },
            "summary": {
                "total_predicted_revenue": 0,
                "total_predicted_revenue_formatted": "₹0",
                "total_predicted_quantity": 0,
                "confidence_level": "Low",
                "data_quality_score": 0
            },
            "weekly_forecast": [],
            "monthly_forecast": [],
            "category_forecast": [],
            "insights": [],
            "model_metrics": {}
        }
        
        if df.empty:
            default_response["insights"] = [{
                "type": "info",
                "title": "Insufficient Data",
                "message": "Upload at least 7 days of sales data to generate forecasts. For accurate predictions, 90+ days is recommended.",
                "icon": "bi bi-info-circle"
            }]
            return default_response
        
        # Check data sufficiency - now allows forecasting with 7+ days but with warnings
        date_range = (df['date'].max() - df['date'].min()).days
        has_limited_data = date_range < 90
        has_very_limited_data = date_range < 30
        has_minimal_data = date_range < 7
        
        # Only block if we have less than 7 days (absolute minimum)
        if has_minimal_data:
            default_response["status"] = "insufficient_data"
            default_response["summary"]["historical_days_used"] = date_range
            default_response["insights"] = [{
                "type": "error",
                "title": "Insufficient Historical Data",
                "message": f"Only {date_range} days of data available. Minimum 7 days required for any forecast.",
                "icon": "bi bi-exclamation-triangle"
            }]
            return default_response
        
        try:
            # Aggregate daily sales for Prophet
            daily_sales = df.groupby(df['date'].dt.date).agg({
                'revenue': 'sum',
                'quantity_sold': 'sum'
            }).reset_index()
            daily_sales.columns = ['ds', 'y', 'quantity']
            daily_sales['ds'] = pd.to_datetime(daily_sales['ds'])
            
            # Revenue forecast
            revenue_df = daily_sales[['ds', 'y']].copy()
            revenue_forecast, revenue_metrics = prophet_manager.forecast_sales(
                revenue_df, periods=90, freq='D'
            )
            
            # Quantity forecast
            quantity_df = daily_sales[['ds', 'quantity']].copy()
            quantity_df.columns = ['ds', 'y']
            quantity_forecast, quantity_metrics = prophet_manager.forecast_sales(
                quantity_df, periods=90, freq='D'
            )
            
            # Extract future predictions only
            future_revenue = revenue_forecast[revenue_forecast['ds'] > now].copy()
            future_quantity = quantity_forecast[quantity_forecast['ds'] > now].copy()
            
            # SAFETY: Ensure all forecast values are non-negative (already done in prophet_service, but double-check)
            future_revenue['yhat'] = future_revenue['yhat'].clip(lower=0)
            future_revenue['yhat_lower'] = future_revenue['yhat_lower'].clip(lower=0)
            future_revenue['yhat_upper'] = future_revenue['yhat_upper'].clip(lower=0)
            future_quantity['yhat'] = future_quantity['yhat'].clip(lower=0)
            future_quantity['yhat_lower'] = future_quantity['yhat_lower'].clip(lower=0)
            future_quantity['yhat_upper'] = future_quantity['yhat_upper'].clip(lower=0)
            
            # Weekly aggregation
            weekly_forecast = []
            for week_num in range(13):  # 13 weeks in a quarter
                week_start = now + timedelta(weeks=week_num)
                week_end = week_start + timedelta(days=6)
                
                week_revenue_data = future_revenue[
                    (future_revenue['ds'] >= week_start) & 
                    (future_revenue['ds'] <= week_end)
                ]
                week_quantity_data = future_quantity[
                    (future_quantity['ds'] >= week_start) & 
                    (future_quantity['ds'] <= week_end)
                ]
                
                if not week_revenue_data.empty:
                    predicted_revenue = max(0, float(week_revenue_data['yhat'].sum()))
                    predicted_quantity = max(0, int(week_quantity_data['yhat'].sum())) if not week_quantity_data.empty else 0
                    weekly_forecast.append({
                        "week_number": week_num + 1,
                        "start_date": week_start.strftime("%Y-%m-%d"),
                        "end_date": week_end.strftime("%Y-%m-%d"),
                        "predicted_revenue": round(predicted_revenue, 2),
                        "predicted_revenue_formatted": f"₹{predicted_revenue:,.0f}",
                        "predicted_quantity": predicted_quantity,
                        "confidence_lower": round(max(0, float(week_revenue_data['yhat_lower'].sum())), 2),
                        "confidence_upper": round(max(0, float(week_revenue_data['yhat_upper'].sum())), 2)
                    })
            
            # Monthly aggregation
            monthly_forecast = []
            for month_num in range(3):  # 3 months
                month_start = now + timedelta(days=month_num * 30)
                month_end = month_start + timedelta(days=29)
                
                month_revenue = future_revenue[
                    (future_revenue['ds'] >= month_start) & 
                    (future_revenue['ds'] <= month_end)
                ]
                month_quantity = future_quantity[
                    (future_quantity['ds'] >= month_start) & 
                    (future_quantity['ds'] <= month_end)
                ]
                
                month_name = month_start.strftime("%B %Y")
                
                if not month_revenue.empty:
                    predicted_revenue = max(0, float(month_revenue['yhat'].sum()))
                    predicted_quantity = max(0, int(month_quantity['yhat'].sum())) if not month_quantity.empty else 0
                    monthly_forecast.append({
                        "month": month_name,
                        "predicted_revenue": round(predicted_revenue, 2),
                        "predicted_revenue_formatted": f"₹{predicted_revenue:,.0f}",
                        "predicted_quantity": predicted_quantity,
                        "confidence_lower": round(max(0, float(month_revenue['yhat_lower'].sum())), 2),
                        "confidence_upper": round(max(0, float(month_revenue['yhat_upper'].sum())), 2)
                    })
            
            # Category-wise forecast (if category data available)
            category_forecast = self._generate_category_forecast(df, revenue_forecast)
            
            # Calculate totals - ensure non-negative
            total_predicted_revenue = max(0, float(future_revenue['yhat'].sum()))
            total_predicted_quantity = max(0, int(future_quantity['yhat'].sum()))
            
            # Get accuracy level and warnings from metrics
            accuracy_level = revenue_metrics.get('accuracy_level', 'Medium')
            has_low_accuracy_warning = revenue_metrics.get('has_low_accuracy_warning', False)
            model_warnings = revenue_metrics.get('warnings', [])
            
            # Override confidence level based on data quality score
            data_quality_score = revenue_metrics.get('data_quality_score', 50)
            if data_quality_score >= 80:
                confidence_level = "High"
            elif data_quality_score >= 60:
                confidence_level = "Medium"
            elif data_quality_score >= 40:
                confidence_level = "Low"
            else:
                confidence_level = "Very Low"
            
            # Generate forecast insights with accuracy warnings
            insights = self._generate_forecast_insights(
                weekly_forecast, monthly_forecast, category_forecast,
                total_predicted_revenue, confidence_level
            )
            
            # Add accuracy warning insights if data is limited
            if has_very_limited_data:
                insights.insert(0, {
                    "type": "warning",
                    "title": "Limited Data Warning",
                    "message": f"This forecast is based on only {date_range} days of data. For accurate predictions, upload at least 90 days of sales history.",
                    "icon": "bi bi-exclamation-triangle",
                    "severity": "high"
                })
            elif has_limited_data:
                insights.insert(0, {
                    "type": "info",
                    "title": "Data Recommendation",
                    "message": f"Forecast based on {date_range} days. More historical data (90+ days) will improve accuracy and seasonal pattern detection.",
                    "icon": "bi bi-info-circle",
                    "severity": "medium"
                })
            
            # Add model-level warnings to insights
            for warning in model_warnings:
                if warning.get('severity') in ['critical', 'high']:
                    insights.append({
                        "type": "warning",
                        "title": "Accuracy Notice",
                        "message": warning.get('message', ''),
                        "icon": "bi bi-exclamation-circle",
                        "severity": warning.get('severity', 'medium')
                    })
            
            forecast_result = {
                "status": "success",
                "forecast_period": {
                    "start": now.strftime("%Y-%m-%d"),
                    "end": quarter_end.strftime("%Y-%m-%d"),
                    "label": "Next Quarter (90 Days)"
                },
                "summary": {
                    "total_predicted_revenue": round(float(total_predicted_revenue), 2),
                    "total_predicted_revenue_formatted": f"₹{total_predicted_revenue:,.0f}",
                    "total_predicted_quantity": int(total_predicted_quantity),
                    "confidence_level": confidence_level,
                    "accuracy_level": accuracy_level,
                    "data_quality_score": data_quality_score,
                    "historical_days_used": date_range,
                    "has_limited_data_warning": has_limited_data,
                    "has_very_limited_data_warning": has_very_limited_data,
                    "minimum_recommended_days": 90,
                    "minimum_required_days": 7
                },
                "weekly_forecast": weekly_forecast,
                "monthly_forecast": monthly_forecast,
                "category_forecast": category_forecast,
                "insights": insights,
                "model_metrics": {
                    "revenue_model": revenue_metrics,
                    "quantity_model": quantity_metrics
                },
                "accuracy_warnings": model_warnings,
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache the result in DB
            self._save_cached_forecast('quarterly', forecast_result)
            
            return forecast_result
            
        except Exception as e:
            logger.error(f"Forecast generation error for shop {self.shop_id}: {e}")
            default_response["status"] = "error"
            default_response["error"] = str(e)
            default_response["insights"] = [{
                "type": "error",
                "title": "Forecast Error",
                "message": "Unable to generate forecast. Please check your data format."
            }]
            return default_response
    
    def _generate_category_forecast(self, historical_df: pd.DataFrame, revenue_forecast: pd.DataFrame) -> List[Dict]:
        """
        Generate category-wise forecast for ALL product categories based on historical data.
        Returns categories sorted by relevance (growing categories first, then by revenue).
        """
        category_forecast = []
        
        category_col = 'category' if 'category' in historical_df.columns else None
        
        # Fallback for legacy data
        if not category_col and 'fabric_type' in historical_df.columns:
            category_col = 'fabric_type'
        
        # Use product_name as fallback if no category
        if not category_col and 'product_name' in historical_df.columns:
            category_col = 'product_name'
        
        if not category_col:
            logger.warning(f"No category column found for shop {self.shop_id}")
            return category_forecast
        
        # Calculate historical category proportions
        category_totals = historical_df.groupby(category_col).agg({
            'revenue': 'sum',
            'quantity_sold': 'sum'
        }).reset_index()
        
        total_historical_revenue = category_totals['revenue'].sum()
        total_historical_qty = category_totals['quantity_sold'].sum()
        
        if total_historical_revenue == 0:
            return category_forecast
        
        # Calculate future revenue total
        now = datetime.now()
        future_revenue_values = revenue_forecast[revenue_forecast['ds'] > now]['yhat'].clip(lower=0)
        future_total = max(0, float(future_revenue_values.sum()))
        
        # Calculate recent data for trend analysis (last 30 days vs previous 30 days)
        recent_30 = historical_df[historical_df['date'] >= now - timedelta(days=30)]
        prev_30 = historical_df[
            (historical_df['date'] >= now - timedelta(days=60)) & 
            (historical_df['date'] < now - timedelta(days=30))
        ]
        
        # Build forecast for each category
        for _, row in category_totals.iterrows():
            category = row[category_col]
            if pd.isna(category) or str(category).strip() == '':
                continue
            
            historical_revenue = row['revenue']
            historical_qty = row['quantity_sold']
            proportion = historical_revenue / total_historical_revenue
            predicted_revenue = future_total * proportion
            
            # Calculate trend based on recent vs previous period performance
            trend = "stable"
            growth_rate = 0
            recent_cat_revenue = recent_30[recent_30[category_col] == category]['revenue'].sum() if not recent_30.empty else 0
            prev_cat_revenue = prev_30[prev_30[category_col] == category]['revenue'].sum() if not prev_30.empty else 0
            
            if prev_cat_revenue > 0:
                growth_rate = ((recent_cat_revenue - prev_cat_revenue) / prev_cat_revenue) * 100
                if growth_rate > 10:
                    trend = "up"
                elif growth_rate < -10:
                    trend = "down"
            elif recent_cat_revenue > 0:
                trend = "up"  # New category with sales
                growth_rate = 100
            
            # Determine actionable insight for shop owner
            insight = None
            priority = 0  # Higher = more important to show
            
            if trend == "up" and proportion >= 0.1:
                insight = "High growth, high volume - prioritize stock"
                priority = 100
            elif trend == "up" and proportion < 0.1:
                insight = "Growing category - consider expanding"
                priority = 80
            elif trend == "down" and proportion >= 0.1:
                insight = "Declining but significant - investigate"
                priority = 90
            elif trend == "down" and proportion < 0.05:
                insight = "Low performer - consider reducing"
                priority = 40
            elif proportion >= 0.15:
                insight = "Top seller - maintain stock levels"
                priority = 70
            
            category_forecast.append({
                "category": str(category).strip(),
                "name": str(category).strip(),  # Alias for frontend compatibility
                "predicted_revenue": round(max(0, float(predicted_revenue)), 2),
                "predicted_revenue_formatted": f"₹{max(0, predicted_revenue):,.0f}",
                "predicted": f"₹{max(0, predicted_revenue):,.0f}",  # Short format for display
                "predicted_quantity": max(0, int(historical_qty * (future_total / total_historical_revenue))) if total_historical_revenue > 0 else 0,
                "proportion_percent": round(proportion * 100, 1),
                "proportion": round(proportion * 100, 1),  # Alias for frontend
                "trend": trend,
                "growth_rate": round(growth_rate, 1),
                "historical_revenue": round(max(0, float(historical_revenue)), 2),
                "insight": insight,
                "priority": priority,
                "is_actionable": priority >= 70  # Flag items shop owner should focus on
            })
        
        # Sort by priority first (actionable items), then by predicted revenue
        category_forecast.sort(key=lambda x: (-x['priority'], -x['predicted_revenue']))
        
        # Return all categories (up to 20) so frontend can decide what to show
        return category_forecast[:20]
    
    def _generate_forecast_insights(
        self, weekly: List, monthly: List, categories: List,
        total_revenue: float, confidence: str
    ) -> List[Dict]:
        """Generate actionable insights from forecast data"""
        insights = []
        
        # Overall forecast insight
        insights.append({
            "type": "info",
            "icon": "bi-calendar-range",
            "title": "Quarterly Projection",
            "message": f"Expected revenue of ₹{total_revenue:,.0f} over the next 90 days ({confidence} confidence)."
        })
        
        # Weekly trend insight
        if len(weekly) >= 4:
            first_month_avg = sum(w['predicted_revenue'] for w in weekly[:4]) / 4
            last_month_avg = sum(w['predicted_revenue'] for w in weekly[-4:]) / 4
            
            if last_month_avg > first_month_avg * 1.1:
                insights.append({
                    "type": "success",
                    "icon": "bi-graph-up",
                    "title": "Upward Trend",
                    "message": "Sales are projected to increase through the quarter. Consider expanding inventory."
                })
            elif last_month_avg < first_month_avg * 0.9:
                insights.append({
                    "type": "warning",
                    "icon": "bi-graph-down",
                    "title": "Downward Trend",
                    "message": "Sales may decline later in the quarter. Plan promotions accordingly."
                })
        
        # Category insight
        if categories and len(categories) > 0:
            top_category = categories[0]
            if top_category['trend'] == 'up':
                insights.append({
                    "type": "success",
                    "icon": "bi-arrow-up-circle",
                    "title": f"{top_category['category']} Growing",
                    "message": f"Your top category is trending upward. Expected: ₹{top_category['predicted_revenue']:,.0f}"
                })
        
        # Peak week insight
        if weekly:
            peak_week = max(weekly, key=lambda x: x['predicted_revenue'])
            insights.append({
                "type": "info",
                "icon": "bi-star",
                "title": "Peak Week Expected",
                "message": f"Week {peak_week['week_number']} ({peak_week['start_date']}) projected as highest with ₹{peak_week['predicted_revenue']:,.0f}"
            })
        
        return insights


# Singleton-style factory function with service caching
_service_cache: Dict[int, SalesAnalyticsService] = {}

def get_sales_analytics_service(shop_id: int, invalidate_cache: bool = False) -> SalesAnalyticsService:
    """
    Get or create sales analytics service for a shop.
    
    Args:
        shop_id: The shop ID
        invalidate_cache: If True, invalidates cached data (use after new upload)
    """
    if shop_id not in _service_cache:
        _service_cache[shop_id] = SalesAnalyticsService(shop_id)
    
    if invalidate_cache:
        _service_cache[shop_id].invalidate_cache()
        _service_cache[shop_id].invalidate_forecasts()  # Also invalidate DB-stored forecasts
    
    return _service_cache[shop_id]


def invalidate_shop_cache(shop_id: int):
    """
    Invalidate all cached data for a shop.
    Call this after new sales data is uploaded.
    """
    _query_cache.invalidate(shop_id)
    if shop_id in _service_cache:
        _service_cache[shop_id].invalidate_cache()
        _service_cache[shop_id].invalidate_forecasts()  # Also invalidate DB-stored forecasts
    else:
        # Create service just to invalidate DB cache
        service = SalesAnalyticsService(shop_id)
        service.invalidate_forecasts()
