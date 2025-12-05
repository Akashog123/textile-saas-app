# backend/shop_exportdata.py
from models.model import db, SalesData, Shop
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

def _format_currency(v):
    try:
        return f"₹{int(round(v))}"
    except:
        return f"₹{v}"

def analyze_series(dates, values):
    """
    Helper to perform statistical analysis on a list of numbers.
    """
    if len(values) < 5:
        return "Not enough data for statistical analysis."
    
    avg = statistics.mean(values)
    try:
        stdev = statistics.stdev(values)
    except:
        return "Data is too uniform for analysis."

    # Anomaly Detection
    outliers = []
    for d, v in zip(dates, values):
        if stdev > 0 and abs(v - avg) / stdev > 1.5:
            type_ = "High Spike" if v > avg else "Significant Drop"
            outliers.append(f"{d} ({type_}: {_format_currency(v)})")
    
    # Stability Check
    cv = (stdev / avg) * 100 if avg > 0 else 0
    stability = "Very Stable" if cv < 10 else "Moderately Volatile" if cv < 30 else "Highly Volatile"
    
    analysis = (
        f"Statistical Analysis: The sales pattern is {stability} (Variation: {int(cv)}%). "
        f"Average daily sales is {_format_currency(avg)}. "
    )
    
    if outliers:
        analysis += f"Detected Anomalies (Unusual Events): {', '.join(outliers)}."
    else:
        analysis += "No significant anomalies detected; sales are consistent."
        
    return analysis

def export_sales_for_shop(shop_id, months=12):
    print(f"[DEBUG] export_sales_for_shop called for Shop {shop_id}")
    docs = []
    try:
        shop = Shop.query.get(shop_id)
        if not shop:
            return []

        # Fetch ALL sales (no date filter in query to ensure we catch everything)
        sales = db.session.query(SalesData).filter(
            SalesData.shop_id == shop_id
        ).order_by(SalesData.date.asc()).all()

        if not sales:
            docs.append({
                'text': f"No sales data available for shop '{shop.name}'.", 
                'source': 'SalesData'
            })
            return docs

        now = datetime.utcnow().date()
        
        # --- TIME CONFIG ---
        last_30_start = now - timedelta(days=30)
        year_start = now - timedelta(days=365)
        
        # --- DATA COLLECTIONS ---
        # 1. Monthly (30 Days) Data
        dates_30d = []
        revenues_30d = []
        graph_points = []
        day_counts = defaultdict(int)
        day_revenues = defaultdict(float)
        total_rev_30d = 0.0

        # 2. Yearly Data
        total_rev_year = 0.0
        total_qty_year = 0
        monthly_breakdown = defaultdict(float) 

        # Pre-fill the last 12 months with 0.0 so the bot sees empty months too
        # This fixes the "no data" issue if only recent sales exist
        for i in range(12):
            d = now - timedelta(days=i*30)
            month_key = d.strftime('%b %Y')
            monthly_breakdown[month_key] = 0.0

        for s in sales:
            try:
                s_date = s.date.date() if isinstance(s.date, datetime) else s.date
                rev = float(getattr(s, 'revenue', 0) or 0)
                qty = int(getattr(s, 'quantity_sold', 0) or 0)

                # --- YEARLY LOGIC (Past 12 Months) ---
                if s_date >= year_start and s_date <= now:
                    total_rev_year += rev
                    total_qty_year += qty
                    month_key = s_date.strftime('%b %Y')
                    monthly_breakdown[month_key] += rev

                # --- MONTHLY LOGIC (Last 30 Days) ---
                if s_date >= last_30_start and s_date <= now:
                    total_rev_30d += rev
                    
                    dates_30d.append(s_date.strftime('%b %d'))
                    revenues_30d.append(rev)
                    graph_points.append(f"{s_date.strftime('%b %d')}: {_format_currency(rev)}")
                    
                    day_name = s_date.strftime('%A')
                    day_counts[day_name] += 1
                    day_revenues[day_name] += rev

            except Exception:
                continue

        # --- INSIGHT GENERATION ---

        # 1. 30-Day Analysis
        stats_insight = analyze_series(dates_30d, revenues_30d)

        day_stats = []
        for day, total in day_revenues.items():
            count = day_counts[day]
            if count > 0:
                avg = total / count
                day_stats.append((day, avg))
        
        day_stats.sort(key=lambda x: x[1], reverse=True)
        if day_stats:
            best = day_stats[0]
            worst = day_stats[-1]
            day_insight = (
                f"Day-of-Week Pattern: Best performing day is {best[0]} (Avg {_format_currency(best[1])}). "
                f"Lowest performing day is {worst[0]} (Avg {_format_currency(worst[1])})."
            )
        else:
            day_insight = "Day-of-Week Pattern: Not enough recent data."

        # 2. Yearly Breakdown Formatting
        # Sort months chronologically so the text flows correctly
        # Helper to parse "Jan 2024" back to date for sorting
        def parse_month_key(k):
            return datetime.strptime(k, '%b %Y')

        sorted_months = sorted(monthly_breakdown.keys(), key=parse_month_key)
        
        # Build the string: "Nov 2024: $500; Dec 2024: $0; Jan 2025: $1200..."
        yearly_summary_list = []
        for m in sorted_months:
            val = monthly_breakdown[m]
            # Only include months within the actual 12-month window to keep text short
            m_date = parse_month_key(m).date()
            if m_date >= year_start.replace(day=1): 
                 yearly_summary_list.append(f"{m}: {_format_currency(val)}")

        yearly_summary_str = "; ".join(yearly_summary_list)


        # --- GENERATE DOCUMENTS ---
        
        # DOC 1: 30-Day Analysis
        graph_trend_str = " -> ".join(graph_points) if graph_points else "No sales in last 30 days."
        docs.append({
            'text': (
                f"DASHBOARD ANALYST REPORT (Last 30 Days): "
                f"Total Revenue: {_format_currency(total_rev_30d)}. "
                f"{stats_insight} "
                f"{day_insight} "
                f"Daily Graph Data: {graph_trend_str}."
            ),
            'source': 'MonthlyGraph'
        })

        # DOC 2: Yearly Overview (Fixed to show all months)
        docs.append({
            'text': (
                f"YEARLY OVERVIEW (Past 12 Months): "
                f"Total Revenue: {_format_currency(total_rev_year)} ({total_qty_year} units). "
                f"Monthly Performance Breakdown: {yearly_summary_str}. "
                "Use this to identify best and worst performing months. "
                "Note: Months with ₹0 had no recorded sales."
            ),
            'source': 'YearlyGraph'
        })

        db.session.close()
        return docs

    except Exception as e:
        print(f"[DEBUG] Error in export: {e}")
        return []