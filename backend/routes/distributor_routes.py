# routes/distributor.py
from flask import Blueprint, jsonify, request, send_file
import pandas as pd
from datetime import datetime
import os
import io
from sqlalchemy import func
from services.ai_providers import get_provider
from utils.auth_utils import token_required, roles_required
from utils.performance_utils import performance_monitor
from utils.file_processing_utils import safe_file_processing, FileProcessingError
from utils.validation import  validate_file_upload
from services.prophet_service import prophet_manager
from services.forecasting_service import (
    compute_regional_summary,
    top_trending_products,
)
from services.ai_service import (
    generate_demand_summary,
    generate_recommendation,
)
from routes.pdf_service import generate_pdf_report
from models.model import db, Product, SalesData, Shop, Inventory, DistributorSupply, User

distributor_bp = Blueprint("distributor", __name__)

# Indian city coordinates for heatmap
INDIAN_CITY_COORDINATES = {
    # Major cities
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Surat": {"lat": 21.1702, "lon": 72.8311},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462},
    "Kanpur": {"lat": 26.4499, "lon": 80.3319},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882},
    "Indore": {"lat": 22.7196, "lon": 75.8577},
    "Thane": {"lat": 19.2183, "lon": 72.9781},
    "Bhopal": {"lat": 23.2599, "lon": 77.4126},
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "Patna": {"lat": 25.5941, "lon": 85.1376},
    "Vadodara": {"lat": 22.3072, "lon": 73.1812},
    "Ghaziabad": {"lat": 28.6692, "lon": 77.4538},
    "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
    "Agra": {"lat": 27.1767, "lon": 78.0081},
    "Nashik": {"lat": 19.9975, "lon": 73.7898},
    "Faridabad": {"lat": 28.4089, "lon": 77.3178},
    "Meerut": {"lat": 28.9845, "lon": 77.7064},
    "Rajkot": {"lat": 22.3039, "lon": 70.8022},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739},
    "Srinagar": {"lat": 34.0837, "lon": 74.7973},
    "Aurangabad": {"lat": 19.8762, "lon": 75.3433},
    "Dhanbad": {"lat": 23.7957, "lon": 86.4304},
    "Amritsar": {"lat": 31.6340, "lon": 74.8723},
    "Navi Mumbai": {"lat": 19.0330, "lon": 73.0297},
    "Allahabad": {"lat": 25.4358, "lon": 81.8463},
    "Prayagraj": {"lat": 25.4358, "lon": 81.8463},
    "Ranchi": {"lat": 23.3441, "lon": 85.3096},
    "Howrah": {"lat": 22.5958, "lon": 88.2636},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
    "Jabalpur": {"lat": 23.1815, "lon": 79.9864},
    "Gwalior": {"lat": 26.2183, "lon": 78.1828},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Jodhpur": {"lat": 26.2389, "lon": 73.0243},
    "Madurai": {"lat": 9.9252, "lon": 78.1198},
    "Raipur": {"lat": 21.2514, "lon": 81.6296},
    "Kota": {"lat": 25.2138, "lon": 75.8648},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362},
    "Solapur": {"lat": 17.6599, "lon": 75.9064},
    "Hubli": {"lat": 15.3647, "lon": 75.1240},
    "Tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
    "Bareilly": {"lat": 28.3670, "lon": 79.4304},
    "Mysore": {"lat": 12.2958, "lon": 76.6394},
    "Mysuru": {"lat": 12.2958, "lon": 76.6394},
    "Tiruppur": {"lat": 11.1085, "lon": 77.3411},
    "Gurgaon": {"lat": 28.4595, "lon": 77.0266},
    "Gurugram": {"lat": 28.4595, "lon": 77.0266},
    "Noida": {"lat": 28.5355, "lon": 77.3910},
    "Salem": {"lat": 11.6643, "lon": 78.1460},
    "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245},
    "Warangal": {"lat": 17.9784, "lon": 79.5941},
    "Guntur": {"lat": 16.3067, "lon": 80.4365},
    "Bikaner": {"lat": 28.0229, "lon": 73.3119},
    "Kochi": {"lat": 9.9312, "lon": 76.2673},
    "Cochin": {"lat": 9.9312, "lon": 76.2673},
    "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
    "Trivandrum": {"lat": 8.5241, "lon": 76.9366},
    # Region names (fallback)
    "North": {"lat": 28.6139, "lon": 77.2090},
    "South": {"lat": 12.9716, "lon": 77.5946},
    "East": {"lat": 22.5726, "lon": 88.3639},
    "West": {"lat": 19.0760, "lon": 72.8777},
    "Central": {"lat": 23.2599, "lon": 77.4126},
}

# Global AI provider
ai_provider = None
try:
    ai_provider = get_provider()
    print(f"Distributor routes AI Provider initialized: {ai_provider.__class__.__name__}")
except Exception as e:
    print(f"Failed to initialize AI provider for distributor routes: {e}")
    ai_provider = None


# POST: Regional Demand & AI Forecast Insights
@distributor_bp.route("/regional-demand", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def get_regional_demand(current_user):
    """
    Generate AI-powered regional demand insights and sales forecasting.
    Combines Prophet forecasting and Gemini AI-generated business insights.
    """
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"status": "error", "message": "No input file provided"}), 400
        
        # Define required columns for sales data
        required_columns = ['Date', 'Region', 'Product', 'Sales', 'Quantity']
        
        # Process file safely with optimizations
        file_result = safe_file_processing(file, file.filename.split('.')[-1], required_columns)
        
        if file_result['status'] == 'error':
            return jsonify({
                "status": "error", 
                "message": file_result['message']
            }), 400
        
        df = file_result['data']
        
        # Log processing stats for monitoring
        print(f"[PERF] Processed {file_result['rows']} rows, {file_result['memory_usage']} bytes")

        # Data processing through forecasting services
        regional_data = compute_regional_summary(df)
        trending_products = top_trending_products(df)
        forecasts = prophet_manager.forecast_sales(df)

        # AI Insights from Gemini
        top_product = trending_products[0]["Product"] if trending_products else "Fabric"
        ai_summary = generate_demand_summary(regional_data, top_product, engine="gemini")
        ai_recommendation = generate_recommendation(regional_data, trending_products, engine="gemini")

        insights = {
            "ai_summary": ai_summary,
            "ai_recommendation": ai_recommendation,
            "regional_share": regional_data,
            "top_products": trending_products,
            "forecast": forecasts,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "analyst": current_user.get("username")
        }

        return jsonify({
            "status": "success",
            "message": "AI regional demand insights generated successfully.",
            "data": insights
        }), 200

    except FileProcessingError as e:
        return jsonify({
            "status": "error",
            "message": f"File processing error: {str(e)}"
        }), 400
    except Exception as e:
        print("Error in /regional-demand:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to generate regional demand insights.",
            "error": str(e)
        }), 500


# POST: Regional Demand Heatmap Data
@distributor_bp.route("/regional-demand-heatmap", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def get_regional_demand_heatmap(current_user):
    """
    Generate interactive heatmap data from uploaded CSV.
    Returns region coordinates with demand intensity for map visualization.
    Expected CSV columns: Date, Product, Region, Sales, Quantity
    """
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"status": "error", "message": "No input file provided"}), 400
        
        # Define required columns for heatmap data
        required_columns = ['Date', 'Region', 'Product', 'Sales', 'Quantity']
        
        # Process file safely
        file_result = safe_file_processing(file, file.filename.split('.')[-1], required_columns)
        
        if file_result['status'] == 'error':
            return jsonify({
                "status": "error", 
                "message": file_result['message']
            }), 400
        
        df = file_result['data']
        
        # Convert Sales and Quantity to numeric
        df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce').fillna(0)
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
        
        # Aggregate data by region
        region_summary = df.groupby('Region').agg({
            'Sales': 'sum',
            'Quantity': 'sum'
        }).reset_index()
        
        # Get top product per region
        top_products_by_region = df.groupby(['Region', 'Product'])['Sales'].sum().reset_index()
        top_products_by_region = top_products_by_region.loc[
            top_products_by_region.groupby('Region')['Sales'].idxmax()
        ][['Region', 'Product']].rename(columns={'Product': 'TopProduct'})
        
        region_summary = region_summary.merge(top_products_by_region, on='Region', how='left')
        
        # Calculate heatmap intensity (normalized 0-1)
        min_sales = region_summary['Sales'].min()
        max_sales = region_summary['Sales'].max()
        if max_sales > min_sales:
            region_summary['Intensity'] = (region_summary['Sales'] - min_sales) / (max_sales - min_sales)
        else:
            region_summary['Intensity'] = 0.5
        
        # Build heatmap points with coordinates
        heatmap_points = []
        for _, row in region_summary.iterrows():
            region_name = row['Region'].strip().title()
            
            # Get coordinates from predefined list
            coords = INDIAN_CITY_COORDINATES.get(region_name)
            if not coords:
                # Try matching with different cases
                for key in INDIAN_CITY_COORDINATES:
                    if key.lower() == region_name.lower():
                        coords = INDIAN_CITY_COORDINATES[key]
                        break
            
            if coords:
                heatmap_points.append({
                    "region": region_name,
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "sales": round(float(row['Sales']), 2),
                    "quantity": int(row['Quantity']),
                    "intensity": round(float(row['Intensity']), 3),
                    "topProduct": row['TopProduct'] if pd.notna(row['TopProduct']) else "N/A"
                })
            else:
                print(f"[Warning] No coordinates found for region: {region_name}")
        
        # Sort by sales descending
        heatmap_points.sort(key=lambda x: x['sales'], reverse=True)
        
        # Calculate summary statistics
        total_sales = float(region_summary['Sales'].sum())
        total_quantity = int(region_summary['Quantity'].sum())
        avg_sales_per_region = float(region_summary['Sales'].mean())
        
        # Determine demand level for each region
        for point in heatmap_points:
            if point['intensity'] >= 0.7:
                point['demandLevel'] = 'high'
                point['color'] = '#dc3545'  # Red - hot
            elif point['intensity'] >= 0.4:
                point['demandLevel'] = 'medium'
                point['color'] = '#ffc107'  # Yellow
            else:
                point['demandLevel'] = 'low'
                point['color'] = '#28a745'  # Green - cool
        
        return jsonify({
            "status": "success",
            "message": "Heatmap data generated successfully",
            "data": {
                "heatmapPoints": heatmap_points,
                "summary": {
                    "totalRegions": len(heatmap_points),
                    "totalSales": round(total_sales, 2),
                    "totalQuantity": total_quantity,
                    "avgSalesPerRegion": round(avg_sales_per_region, 2),
                    "highDemandRegions": len([p for p in heatmap_points if p['demandLevel'] == 'high']),
                    "mediumDemandRegions": len([p for p in heatmap_points if p['demandLevel'] == 'medium']),
                    "lowDemandRegions": len([p for p in heatmap_points if p['demandLevel'] == 'low'])
                },
                "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }), 200

    except FileProcessingError as e:
        return jsonify({
            "status": "error",
            "message": f"File processing error: {str(e)}"
        }), 400
    except Exception as e:
        print("Error in /regional-demand-heatmap:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to generate heatmap data.",
            "error": str(e)
        }), 500


# GET: Stock Heatmap Data from Database (for logged-in distributor)
@distributor_bp.route("/stock-heatmap", methods=["GET"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def get_stock_heatmap(current_user):
    """
    Get stock levels for shops supplied by the current distributor.
    Returns shop locations with stock health status for heatmap visualization.
    Stock health is determined by comparing qty_available vs safety_stock.
    Now includes product-level details and sales performance data.
    """
    try:
        distributor_id = current_user.get("id")
        
        if not distributor_id:
            return jsonify({"status": "error", "message": "User ID not found"}), 400
        
        # Get all products this distributor supplies and to which shops
        distributor_supplies = db.session.query(
            DistributorSupply.shop_id,
            DistributorSupply.product_id,
            DistributorSupply.quantity_supplied,
            DistributorSupply.unit_price,
            DistributorSupply.status
        ).filter(
            DistributorSupply.distributor_id == distributor_id
        ).all()
        
        if not distributor_supplies:
            return jsonify({
                "status": "success",
                "message": "No shops found for this distributor",
                "data": {
                    "heatmapPoints": [],
                    "criticalProducts": [],
                    "productSummary": {},
                    "summary": {
                        "totalShops": 0,
                        "criticalStockShops": 0,
                        "lowStockShops": 0,
                        "healthyStockShops": 0,
                        "totalProducts": 0,
                        "totalStockValue": 0,
                        "criticalProductCount": 0,
                        "lowProductCount": 0
                    },
                    "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            }), 200
        
        # Build lookup of which products go to which shops
        shop_product_map = {}  # shop_id -> list of product_ids
        product_supply_info = {}  # product_id -> supply info
        for supply in distributor_supplies:
            if supply.shop_id not in shop_product_map:
                shop_product_map[supply.shop_id] = []
            shop_product_map[supply.shop_id].append(supply.product_id)
            product_supply_info[supply.product_id] = {
                'quantity_supplied': supply.quantity_supplied,
                'unit_price': supply.unit_price,
                'status': supply.status
            }
        
        shop_ids = list(shop_product_map.keys())
        product_ids = list(set([p for products in shop_product_map.values() for p in products]))
        
        # Get shops with their details
        shops = Shop.query.filter(Shop.id.in_(shop_ids)).all()
        shops_dict = {s.id: s for s in shops}
        
        # Get all relevant products
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        products_dict = {p.id: p for p in products}
        
        # Get inventory for all relevant products
        inventories = Inventory.query.filter(Inventory.product_id.in_(product_ids)).all()
        inventory_dict = {i.product_id: i for i in inventories}
        
        # Get sales data for these products (aggregate sales performance - units only, not revenue)
        sales_data = db.session.query(
            SalesData.product_id,
            SalesData.shop_id,
            func.sum(SalesData.quantity_sold).label('total_sold'),
            func.count(SalesData.id).label('transaction_count')
        ).filter(
            SalesData.product_id.in_(product_ids)
        ).group_by(SalesData.product_id, SalesData.shop_id).all()
        
        # Build sales lookup: (product_id, shop_id) -> sales info (no revenue - privacy)
        sales_lookup = {}
        for sale in sales_data:
            key = (sale.product_id, sale.shop_id)
            sales_lookup[key] = {
                'total_sold': sale.total_sold or 0,
                'transaction_count': sale.transaction_count or 0
            }
        
        heatmap_points = []
        all_critical_products = []
        all_low_products = []
        total_products = 0
        total_stock_value = 0
        
        for shop_id, supplied_product_ids in shop_product_map.items():
            shop = shops_dict.get(shop_id)
            if not shop:
                continue
            
            # Calculate stock health for products supplied to this shop
            shop_stock_data = []
            critical_products = []
            low_products = []
            critical_count = 0
            low_count = 0
            healthy_count = 0
            shop_total_stock = 0
            shop_total_value = 0
            shop_total_sold = 0
            
            for product_id in set(supplied_product_ids):  # Remove duplicates
                product = products_dict.get(product_id)
                if not product:
                    continue
                    
                inventory = inventory_dict.get(product_id)
                supply_info = product_supply_info.get(product_id, {})
                sales_info = sales_lookup.get((product_id, shop_id), {'total_sold': 0, 'transaction_count': 0})
                
                qty_available = inventory.qty_available if inventory else 0
                safety_stock = inventory.safety_stock if inventory else 0
                
                # Determine stock health
                if safety_stock > 0:
                    stock_ratio = qty_available / safety_stock
                else:
                    stock_ratio = 1.0 if qty_available > 0 else 0
                
                # Categorize: critical (<50% of safety), low (50-100% of safety), healthy (>100%)
                if stock_ratio < 0.5:
                    critical_count += 1
                    status = 'critical'
                elif stock_ratio < 1.0:
                    low_count += 1
                    status = 'low'
                else:
                    healthy_count += 1
                    status = 'healthy'
                
                shop_total_stock += qty_available
                shop_total_value += float(product.price or 0) * qty_available
                shop_total_sold += sales_info['total_sold']
                
                product_detail = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "qty_available": qty_available,
                    "safety_stock": safety_stock,
                    "stock_ratio": round(stock_ratio, 2),
                    "status": status,
                    "price": float(product.price or 0),
                    "quantity_supplied": supply_info.get('quantity_supplied', 0),
                    "total_sold": sales_info['total_sold'],
                    "sell_through_rate": round((sales_info['total_sold'] / supply_info.get('quantity_supplied', 1)) * 100, 1) if supply_info.get('quantity_supplied', 0) > 0 else 0
                }
                
                shop_stock_data.append(product_detail)
                
                # Track critical and low products for global list
                if status == 'critical':
                    critical_products.append({
                        **product_detail,
                        "shop_id": shop_id,
                        "shop_name": shop.name,
                        "region": shop.city or "Unknown"
                    })
                elif status == 'low':
                    low_products.append({
                        **product_detail,
                        "shop_id": shop_id,
                        "shop_name": shop.name,
                        "region": shop.city or "Unknown"
                    })
            
            # Sort stock data by status priority (critical first) then by stock ratio
            status_priority = {'critical': 0, 'low': 1, 'healthy': 2}
            shop_stock_data.sort(key=lambda x: (status_priority.get(x['status'], 3), x['stock_ratio']))
            
            all_critical_products.extend(critical_products)
            all_low_products.extend(low_products)
            
            total_products += len(set(supplied_product_ids))
            total_stock_value += shop_total_value
            
            # Calculate overall shop stock health score (0-1, lower is worse)
            total_items = critical_count + low_count + healthy_count
            if total_items > 0:
                # Weighted score: critical=0, low=0.5, healthy=1
                health_score = (critical_count * 0 + low_count * 0.5 + healthy_count * 1) / total_items
            else:
                health_score = 1.0
            
            # Determine stock level for color coding
            if health_score < 0.5:
                stock_level = 'critical'
                color = '#dc3545'  # Red
            elif health_score < 0.8:
                stock_level = 'low'
                color = '#ffc107'  # Yellow
            else:
                stock_level = 'healthy'
                color = '#28a745'  # Green
            
            # Get top selling product for this shop
            top_selling = max(shop_stock_data, key=lambda x: x['total_sold']) if shop_stock_data else None
            top_product_name = top_selling['product_name'] if top_selling else "N/A"
            
            # Use shop coordinates or fallback to city coordinates
            lat = shop.lat
            lon = shop.lon
            
            if not lat or not lon:
                city = (shop.city or "").strip().title()
                coords = INDIAN_CITY_COORDINATES.get(city)
                if coords:
                    lat = coords["lat"]
                    lon = coords["lon"]
                else:
                    lat = 20.5937
                    lon = 78.9629
            
            heatmap_points.append({
                "shopId": shop.id,
                "shopName": shop.name,
                "region": shop.city or "Unknown",
                "lat": lat,
                "lon": lon,
                "totalProducts": len(set(supplied_product_ids)),
                "totalStock": shop_total_stock,
                "stockValue": round(shop_total_value, 2),
                "totalSold": shop_total_sold,
                "criticalItems": critical_count,
                "lowItems": low_count,
                "healthyItems": healthy_count,
                "healthScore": round(health_score, 2),
                "stockLevel": stock_level,
                "color": color,
                "topProduct": top_product_name,
                "criticalProducts": [p['product_name'] for p in critical_products[:3]],
                "lowProducts": [p['product_name'] for p in low_products[:3]],
                "stockDetails": shop_stock_data  # All products with full details
            })
        
        # Sort heatmap points by health score (worst first)
        heatmap_points.sort(key=lambda x: x['healthScore'])
        
        # Sort critical products by stock ratio (most critical first)
        all_critical_products.sort(key=lambda x: x['stock_ratio'])
        all_low_products.sort(key=lambda x: x['stock_ratio'])
        
        # Calculate summary
        critical_shops = len([p for p in heatmap_points if p['stockLevel'] == 'critical'])
        low_shops = len([p for p in heatmap_points if p['stockLevel'] == 'low'])
        healthy_shops = len([p for p in heatmap_points if p['stockLevel'] == 'healthy'])
        
        # Build product category summary
        category_summary = {}
        for p in all_critical_products + all_low_products:
            cat = p.get('category', 'Unknown')
            if cat not in category_summary:
                category_summary[cat] = {'critical': 0, 'low': 0}
            if p['status'] == 'critical':
                category_summary[cat]['critical'] += 1
            else:
                category_summary[cat]['low'] += 1
        
        return jsonify({
            "status": "success",
            "message": "Stock heatmap data generated successfully",
            "data": {
                "heatmapPoints": heatmap_points,
                "criticalProducts": all_critical_products[:20],  # Top 20 most critical
                "lowProducts": all_low_products[:15],  # Top 15 low stock
                "categorySummary": category_summary,
                "summary": {
                    "totalShops": len(heatmap_points),
                    "criticalStockShops": critical_shops,
                    "lowStockShops": low_shops,
                    "healthyStockShops": healthy_shops,
                    "totalProducts": total_products,
                    "totalStockValue": round(total_stock_value, 2),
                    "criticalProductCount": len(all_critical_products),
                    "lowProductCount": len(all_low_products)
                },
                "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }), 200
        
    except Exception as e:
        print("Error in /stock-heatmap:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Failed to generate stock heatmap data.",
            "error": str(e)
        }), 500


# GET: Product Performance Data for Distributor
@distributor_bp.route("/product-performance", methods=["GET"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def get_product_performance(current_user):
    """
    Get detailed product performance data for the current distributor.
    Shows sales data for products the distributor supplies across all shops.
    Respects shop privacy by only showing aggregate metrics, not shop-specific financials.
    """
    try:
        distributor_id = current_user.get("id")
        
        if not distributor_id:
            return jsonify({"status": "error", "message": "User ID not found"}), 400
        
        # Get all products this distributor supplies
        distributor_supplies = db.session.query(
            DistributorSupply.product_id,
            DistributorSupply.shop_id,
            DistributorSupply.quantity_supplied,
            DistributorSupply.unit_price,
            DistributorSupply.total_value,
            DistributorSupply.supply_date,
            DistributorSupply.status
        ).filter(
            DistributorSupply.distributor_id == distributor_id
        ).all()
        
        if not distributor_supplies:
            return jsonify({
                "status": "success",
                "message": "No supply data found",
                "data": {
                    "products": [],
                    "topPerformers": [],
                    "lowPerformers": [],
                    "summary": {
                        "totalProducts": 0,
                        "totalSupplied": 0,
                        "totalSold": 0,
                        "avgSellThrough": 0
                    },
                    "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
            }), 200
        
        # Build supply lookup
        product_supply = {}  # product_id -> {total_supplied, shops, ...}
        all_product_ids = set()
        all_shop_ids = set()
        
        for supply in distributor_supplies:
            all_product_ids.add(supply.product_id)
            all_shop_ids.add(supply.shop_id)
            
            if supply.product_id not in product_supply:
                product_supply[supply.product_id] = {
                    'total_supplied': 0,
                    'total_value': 0,
                    'shops': set(),
                    'unit_price': supply.unit_price or 0
                }
            product_supply[supply.product_id]['total_supplied'] += supply.quantity_supplied or 0
            product_supply[supply.product_id]['total_value'] += float(supply.total_value or 0)
            product_supply[supply.product_id]['shops'].add(supply.shop_id)
        
        # Get product details
        products = Product.query.filter(Product.id.in_(list(all_product_ids))).all()
        products_dict = {p.id: p for p in products}
        
        # Get shop names
        shops = Shop.query.filter(Shop.id.in_(list(all_shop_ids))).all()
        shops_dict = {s.id: s.name for s in shops}
        
        # Get inventory for all products
        inventories = Inventory.query.filter(Inventory.product_id.in_(list(all_product_ids))).all()
        inventory_dict = {i.product_id: i for i in inventories}
        
        # Get aggregated sales data for these products (units only, not revenue - privacy)
        sales_data = db.session.query(
            SalesData.product_id,
            func.sum(SalesData.quantity_sold).label('total_sold'),
            func.count(SalesData.id).label('transaction_count'),
            func.avg(SalesData.quantity_sold).label('avg_quantity'),
            func.max(SalesData.date).label('last_sale_date')
        ).filter(
            SalesData.product_id.in_(list(all_product_ids))
        ).group_by(SalesData.product_id).all()
        
        # Build sales lookup (no revenue - shop owner's private data)
        sales_lookup = {}
        for sale in sales_data:
            sales_lookup[sale.product_id] = {
                'total_sold': sale.total_sold or 0,
                'transaction_count': sale.transaction_count or 0,
                'avg_quantity': float(sale.avg_quantity or 0),
                'last_sale_date': sale.last_sale_date.strftime("%Y-%m-%d") if sale.last_sale_date else None
            }
        
        # Build product performance list
        product_performance = []
        total_supplied = 0
        total_sold = 0
        
        for product_id, supply_info in product_supply.items():
            product = products_dict.get(product_id)
            if not product:
                continue
            
            inventory = inventory_dict.get(product_id)
            sales = sales_lookup.get(product_id, {
                'total_sold': 0,
                'transaction_count': 0,
                'avg_quantity': 0,
                'last_sale_date': None
            })
            
            qty_supplied = supply_info['total_supplied']
            qty_sold = sales['total_sold']
            
            # Calculate sell-through rate
            sell_through = (qty_sold / qty_supplied * 100) if qty_supplied > 0 else 0
            
            # Determine performance level
            if sell_through >= 80:
                performance = 'excellent'
            elif sell_through >= 50:
                performance = 'good'
            elif sell_through >= 25:
                performance = 'average'
            else:
                performance = 'poor'
            
            # Determine stock status
            qty_available = inventory.qty_available if inventory else 0
            safety_stock = inventory.safety_stock if inventory else 0
            stock_ratio = qty_available / safety_stock if safety_stock > 0 else 1.0
            
            if stock_ratio < 0.5:
                stock_status = 'critical'
            elif stock_ratio < 1.0:
                stock_status = 'low'
            else:
                stock_status = 'healthy'
            
            product_performance.append({
                "product_id": product_id,
                "product_name": product.name,
                "category": product.category,
                "price": float(product.price or 0),
                "qty_supplied": qty_supplied,
                "qty_sold": qty_sold,
                "qty_available": qty_available,
                "safety_stock": safety_stock,
                "supply_value": round(supply_info['total_value'], 2),
                "sell_through_rate": round(sell_through, 1),
                "performance": performance,
                "stock_status": stock_status,
                "stock_ratio": round(stock_ratio, 2),
                "shops_count": len(supply_info['shops']),
                "shop_names": [shops_dict.get(sid, f"Shop {sid}") for sid in supply_info['shops']],
                "transaction_count": sales['transaction_count'],
                "avg_quantity_per_sale": round(sales['avg_quantity'], 1),
                "last_sale_date": sales['last_sale_date']
            })
            
            total_supplied += qty_supplied
            total_sold += qty_sold
        
        # Sort by sell-through rate descending
        product_performance.sort(key=lambda x: x['sell_through_rate'], reverse=True)
        
        # Get top and low performers
        top_performers = [p for p in product_performance if p['performance'] in ['excellent', 'good']][:10]
        low_performers = sorted([p for p in product_performance if p['performance'] in ['poor', 'average']], 
                                key=lambda x: x['sell_through_rate'])[:10]
        
        # Calculate averages
        avg_sell_through = (total_sold / total_supplied * 100) if total_supplied > 0 else 0
        
        # Category breakdown (by units sold, not revenue)
        category_performance = {}
        for p in product_performance:
            cat = p['category'] or 'Unknown'
            if cat not in category_performance:
                category_performance[cat] = {
                    'products': 0,
                    'supplied': 0,
                    'sold': 0
                }
            category_performance[cat]['products'] += 1
            category_performance[cat]['supplied'] += p['qty_supplied']
            category_performance[cat]['sold'] += p['qty_sold']
        
        # Add sell-through rate to each category
        for cat in category_performance:
            cat_data = category_performance[cat]
            cat_data['sell_through_rate'] = round(
                (cat_data['sold'] / cat_data['supplied'] * 100) if cat_data['supplied'] > 0 else 0, 1
            )
        
        return jsonify({
            "status": "success",
            "message": "Product performance data generated successfully",
            "data": {
                "products": product_performance,
                "topPerformers": top_performers,
                "lowPerformers": low_performers,
                "categoryPerformance": category_performance,
                "summary": {
                    "totalProducts": len(product_performance),
                    "totalSupplied": total_supplied,
                    "totalSold": total_sold,
                    "avgSellThrough": round(avg_sell_through, 1),
                    "excellentPerformers": len([p for p in product_performance if p['performance'] == 'excellent']),
                    "goodPerformers": len([p for p in product_performance if p['performance'] == 'good']),
                    "averagePerformers": len([p for p in product_performance if p['performance'] == 'average']),
                    "poorPerformers": len([p for p in product_performance if p['performance'] == 'poor'])
                },
                "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }), 200
        
    except Exception as e:
        print("Error in /product-performance:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Failed to generate product performance data.",
            "error": str(e)
        }), 500


# GET: Sample Input Format for Distributor CSV
@distributor_bp.route("/sample-format", methods=["GET"])
def get_sample_format():
    """
    Provide a downloadable example structure for distributor uploads.
    Helps ensure users upload valid data for forecasting.
    """
    try:
        sample_data = {
            "Region": ["North", "South", "East", "West"],
            "Product": ["Silk", "Cotton", "Linen", "Wool"],
            "Date": ["2025-10-01", "2025-10-08", "2025-10-15", "2025-10-22"],
            "Sales": [5000, 3000, 4000, 2000]
        }
        return jsonify({
            "status": "success",
            "sample_structure": sample_data,
            "instructions": "Ensure your uploaded CSV/XLSX contains Region, Product, Date, and Sales columns."
        }), 200
    except Exception as e:
        print("Error generating sample format:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# Gemini Helper: AI-Generated Production Insight
def _generate_production_ai_summary(df, forecast_df):
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

        if not ai_provider:
            return "AI provider not configured for production insights."

        result = ai_provider.generate_text(summary_prompt)

        return result if result else (
            "Increase silk and cotton; maintain linen; reduce wool production due to declining demand."
        )

    except Exception as exc:
        print("[AI Production Plan Error]", exc)
        return "Unable to generate AI insights currently."


# POST: Production Planning (embedded implementation)
@distributor_bp.route("/production-plan", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
def distributor_production_plan(current_user):
    """Upload sales CSV and get AI-powered production planning insights."""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
        # Validate file upload
        is_valid, message = validate_file_upload(file, ['.csv', '.xlsx', '.xls'], max_size_mb=16)
        if not is_valid:
            return jsonify({"status": "error", "message": message}), 400

        filename = (file.filename or "").lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({"status": "error", "message": "File must be .csv or .xlsx"}), 400

        if df.empty:
            return jsonify({"status": "error", "message": "Uploaded file has no rows"}), 400

        required_cols = {"Date", "Product", "Sales"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            return jsonify({
                "status": "error",
                "message": f"File must contain columns: {', '.join(sorted(required_cols))}",
                "missing": sorted(missing)
            }), 400

        df["ds"] = pd.to_datetime(df["Date"], errors="coerce")
        df["y"] = pd.to_numeric(df["Sales"], errors="coerce")
        df.dropna(subset=["ds", "y"], inplace=True)

        if df.empty:
            return jsonify({"status": "error", "message": "No valid Date/Sales rows after parsing"}), 400

        # Use optimized Prophet service
        try:
            forecast_data, metrics = prophet_manager.forecast_sales(df[["ds", "y"]], periods=30)
            
            # Convert back to expected format for AI summary
            forecast = pd.DataFrame({
                'ds': forecast_data['ds'],
                'yhat': forecast_data['yhat'],
                'yhat_lower': forecast_data['yhat_lower'],
                'yhat_upper': forecast_data['yhat_upper']
            })
            
            print(f"[Optimized Prophet] Forecast generated in {metrics.get('forecast_time_seconds', 0):.2f}s")
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Forecasting failed: {str(e)}"}), 500

        ai_summary = _generate_production_ai_summary(df, forecast)

        top_products = (
            df.groupby("Product")["Sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )
        underperforming = (
            df.groupby("Product")["Sales"]
            .sum()
            .sort_values(ascending=True)
            .head(5)
            .reset_index()
        )

        ai_priorities = []
        for _, row in top_products.iterrows():
            ai_priorities.append({
                "title": f"Increase Production: {row['Product']}",
                "detail": f"High sales of ₹{row['Sales']:,}. Forecast predicts upward trend.",
                "level": "increase",
            })
        for _, row in underperforming.iterrows():
            ai_priorities.append({
                "title": f"Reduce Production: {row['Product']}",
                "detail": f"Low sales (₹{row['Sales']:,}). Consider seasonal adjustments.",
                "level": "reduce",
            })

        return jsonify({
            "status": "success",
            "ai_summary": ai_summary,
            "ai_priorities": ai_priorities[:5],
            "top_selling": [
                {
                    "name": row["Product"],
                    "growth": f"+{round((row['Sales'] / df['Sales'].mean()) * 10, 1)}% MoM",
                    "volume": f"{row['Sales']} meters",
                    "image": "https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9"
                } for _, row in top_products.iterrows()
            ],
            "underperforming": [
                {
                    "name": row["Product"],
                    "decline": f"-{round((1 - row['Sales'] / df['Sales'].mean()) * 10, 1)}%",
                    "volume": int(row["Sales"]),
                    "image": "https://images.unsplash.com/photo-1636545732552-a94515d1b4c0"
                } for _, row in underperforming.iterrows()
            ]
        }), 200

    except Exception as exc:
        print("[Error - Production Plan]", exc)
        return jsonify({
            "status": "error",
            "message": "Failed to generate production plan.",
            "error": str(exc)
        }), 500


# GET: Export Production Plan CSV (embedded implementation)
@distributor_bp.route("/export-plan", methods=["GET"])
@token_required
@roles_required('distributor', 'manufacturer')
def distributor_export_plan(current_user):
    """Export a production plan CSV derived from live sales data."""
    try:
        window_start = datetime.utcnow().date().replace(day=1)
        sales_rows = (
            SalesData.query
            .filter(SalesData.date >= window_start)
            .all()
        )

        if not sales_rows:
            return jsonify({
                "status": "error",
                "message": "No sales data available for export this month."
            }), 404

        product_ids = {row.product_id for row in sales_rows if row.product_id}
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        product_lookup = {p.id: p for p in products}

        rows = []
        for entry in sales_rows:
            product = product_lookup.get(entry.product_id)
            rows.append({
                "Product": product.name if product else f"Product #{entry.product_id}",
                "Category": product.category if product else "Unknown",
                "Region": entry.region or "Unknown",
                "Revenue": float(entry.revenue or 0),
                "UnitsSold": entry.quantity_sold or 0
            })

        df = pd.DataFrame(rows)
        summary = (
            df.groupby(["Product", "Category"])
            .agg({"Revenue": "sum", "UnitsSold": "sum"})
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )

        csv_buf = io.StringIO()
        summary.to_csv(csv_buf, index=False)
        csv_buf.seek(0)

        return send_file(
            io.BytesIO(csv_buf.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="production_plan.csv",
        )
    except Exception as exc:
        print("[Error - Export Plan]", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


# GET: Regional Demand Report PDF (AI Summary)
@distributor_bp.route("/regional-report", methods=["GET"])
@token_required
@roles_required('distributor', 'manufacturer')  
def generate_regional_report(current_user):
    """
    Generates a downloadable PDF summary of AI insights and forecast data.
    """
    try:
        username = getattr(current_user, "username", None)
        if not username and isinstance(current_user, dict):
            username = current_user.get("username")

        pdf_buffer = generate_pdf_report(
            title="Regional Demand Report",
            subtitle=f"Prepared by {username} | {datetime.now().strftime('%d-%b-%Y')}",
            summary="AI-driven demand insights indicate strong growth in the South region with upward trends in Cotton and Linen sales."
        )

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="Regional_Demand_Report.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print("PDF generation failed:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# GET: Prophet Model Performance Metrics
@distributor_bp.route("/prophet-metrics", methods=["GET"])
@token_required
@performance_monitor
def get_prophet_metrics(current_user):
    """Get Prophet model performance and cache statistics"""
    try:
        cache_stats = prophet_manager.get_cache_stats()
        
        return jsonify({
            "status": "success",
            "prophet_metrics": {
                "cached_models": cache_stats["cached_models"],
                "max_cache_size": cache_stats["max_cache_size"],
                "cache_hit_ratio": cache_stats["cache_hit_ratio"],
                "memory_usage_estimate_mb": cache_stats["memory_usage_estimate"],
                "optimization_features": {
                    "textile_seasonality": True,
                    "outlier_detection": True,
                    "data_validation": True,
                    "model_caching": True,
                    "performance_monitoring": True
                },
                "configuration": {
                    "weekly_seasonality": True,
                    "yearly_seasonality": True,
                    "daily_seasonality": False,
                    "changepoint_prior_scale": 0.05,
                    "seasonality_prior_scale": 10.0,
                    "interval_width": 0.8
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to get metrics: {str(e)}"}), 500


# POST: Clear Prophet Model Cache
@distributor_bp.route("/prophet-cache-clear", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
def clear_prophet_cache(current_user):
    """Clear Prophet model cache (admin operation)"""
    try:
        prophet_manager.clear_cache()
        
        return jsonify({
            "status": "success",
            "message": "Prophet model cache cleared successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to clear cache: {str(e)}"}), 500


# POST: AI-Powered Production Planning from Heatmap Data
@distributor_bp.route("/ai-production-planning", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def ai_production_planning(current_user):
    """
    Generate comprehensive AI-powered production planning insights.
    Uses the heatmap data already analyzed to provide:
    - Demand forecasting
    - Stock replenishment recommendations
    - Production priority matrix
    - Regional marketing insights
    - Personalized promotion suggestions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        heatmap_points = data.get('heatmapPoints', [])
        summary = data.get('summary', {})
        
        if not heatmap_points:
            return jsonify({"status": "error", "message": "No heatmap data provided"}), 400
        
        # Extract key metrics from heatmap data
        total_sales = summary.get('totalSales', 0)
        total_quantity = summary.get('totalQuantity', 0)
        total_regions = summary.get('totalRegions', 0)
        high_demand_count = summary.get('highDemandRegions', 0)
        medium_demand_count = summary.get('mediumDemandRegions', 0)
        low_demand_count = summary.get('lowDemandRegions', 0)
        
        # Analyze regions by demand level
        high_demand_regions = [p for p in heatmap_points if p.get('demandLevel') == 'high']
        medium_demand_regions = [p for p in heatmap_points if p.get('demandLevel') == 'medium']
        low_demand_regions = [p for p in heatmap_points if p.get('demandLevel') == 'low']
        
        # Get top products across regions
        product_sales = {}
        for point in heatmap_points:
            product = point.get('topProduct', 'Unknown')
            sales = point.get('sales', 0)
            if product in product_sales:
                product_sales[product] += sales
            else:
                product_sales[product] = sales
        
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
        top_products = sorted_products[:5] if len(sorted_products) >= 5 else sorted_products
        low_products = sorted_products[-3:] if len(sorted_products) >= 3 else []
        
        # Generate AI insights using Gemini
        ai_insights = _generate_planning_ai_insights(
            heatmap_points, summary, high_demand_regions, 
            medium_demand_regions, low_demand_regions, 
            top_products, low_products
        )
        
        # Build demand forecast (simulate based on current data)
        demand_forecast = []
        for point in sorted(heatmap_points, key=lambda x: x.get('sales', 0), reverse=True)[:10]:
            # Simulate growth trend based on demand level
            if point.get('demandLevel') == 'high':
                trend = 'rising'
                growth_rate = round(15 + (point.get('intensity', 0.5) * 20), 1)
            elif point.get('demandLevel') == 'medium':
                trend = 'stable'
                growth_rate = round(5 + (point.get('intensity', 0.5) * 10), 1)
            else:
                trend = 'falling'
                growth_rate = round(-5 - ((1 - point.get('intensity', 0.5)) * 15), 1)
            
            demand_forecast.append({
                "region": point.get('region'),
                "currentSales": point.get('sales', 0),
                "projectedSales30d": round(point.get('sales', 0) * (1 + growth_rate/100), 2),
                "projectedSales60d": round(point.get('sales', 0) * (1 + growth_rate/100 * 2), 2),
                "projectedSales90d": round(point.get('sales', 0) * (1 + growth_rate/100 * 3), 2),
                "trend": trend,
                "growthRate": growth_rate,
                "topProduct": point.get('topProduct', 'N/A')
            })
        
        # Build stock replenishment recommendations
        stock_recommendations = []
        for i, point in enumerate(sorted(heatmap_points, key=lambda x: x.get('sales', 0), reverse=True)):
            if point.get('demandLevel') == 'high':
                priority = 'urgent'
                action = 'Immediate restocking required'
                reorder_qty = int(point.get('quantity', 0) * 1.5)
            elif point.get('demandLevel') == 'medium':
                priority = 'high' if i < len(heatmap_points) // 3 else 'medium'
                action = 'Schedule restocking this week'
                reorder_qty = int(point.get('quantity', 0) * 1.2)
            else:
                priority = 'low'
                action = 'Monitor inventory levels'
                reorder_qty = int(point.get('quantity', 0) * 0.8)
            
            stock_recommendations.append({
                "region": point.get('region'),
                "product": point.get('topProduct', 'N/A'),
                "currentStock": point.get('quantity', 0),
                "recommendedReorder": reorder_qty,
                "priority": priority,
                "action": action
            })
        
        # Build production priority matrix
        production_priorities = {
            "increase": [],
            "maintain": [],
            "reduce": []
        }
        
        for product, sales in top_products[:3]:
            production_priorities["increase"].append({
                "product": product,
                "sales": round(sales, 2),
                "reason": f"High demand with ₹{sales:,.0f} total sales across regions"
            })
        
        for product, sales in sorted_products[3:6] if len(sorted_products) > 3 else []:
            production_priorities["maintain"].append({
                "product": product,
                "sales": round(sales, 2),
                "reason": f"Stable demand with consistent sales performance"
            })
        
        for product, sales in low_products:
            production_priorities["reduce"].append({
                "product": product,
                "sales": round(sales, 2),
                "reason": f"Low demand - consider promotional campaigns or inventory reduction"
            })
        
        # Build regional marketing insights
        marketing_insights = []
        for point in high_demand_regions[:5]:
            marketing_insights.append({
                "region": point.get('region'),
                "insight": f"High potential market - focus premium product campaigns",
                "recommendedAction": f"Launch targeted ads for {point.get('topProduct', 'top products')}",
                "potentialRevenue": round(point.get('sales', 0) * 1.3, 2),
                "priority": "high"
            })
        
        for point in low_demand_regions[:3]:
            marketing_insights.append({
                "region": point.get('region'),
                "insight": "Underperforming market - promotional push needed",
                "recommendedAction": f"Offer discounts on {point.get('topProduct', 'slow-moving items')}",
                "potentialRevenue": round(point.get('sales', 0) * 1.5, 2),
                "priority": "medium"
            })
        
        # Build promotion planner
        promotions = []
        
        # Seasonal promotions for high-demand products
        for product, sales in top_products[:2]:
            promotions.append({
                "type": "premium",
                "title": f"Premium Collection: {product}",
                "description": f"Highlight top-selling {product} with exclusive packaging",
                "targetRegions": [r.get('region') for r in high_demand_regions[:3]],
                "expectedROI": "25-35%",
                "duration": "2 weeks"
            })
        
        # Clearance promotions for low-demand products
        for product, sales in low_products[:2]:
            promotions.append({
                "type": "clearance",
                "title": f"Clearance Sale: {product}",
                "description": f"Offer 20-30% discount to clear {product} inventory",
                "targetRegions": [r.get('region') for r in low_demand_regions],
                "expectedROI": "10-15%",
                "duration": "1 week"
            })
        
        # Regional expansion promotion
        if medium_demand_regions:
            promotions.append({
                "type": "expansion",
                "title": "Regional Market Expansion",
                "description": "Target medium-demand regions with introductory offers",
                "targetRegions": [r.get('region') for r in medium_demand_regions[:4]],
                "expectedROI": "15-20%",
                "duration": "1 month"
            })
        
        # Build summary cards data
        summary_cards = {
            "totalProjectedDemand": round(total_sales * 1.15, 2),  # 15% growth projection
            "topProducts": [p[0] for p in top_products[:3]],
            "topRegions": [r.get('region') for r in high_demand_regions[:3]],
            "urgentActions": len([s for s in stock_recommendations if s['priority'] == 'urgent']),
            "weeklyTasks": [
                f"Restock {top_products[0][0] if top_products else 'top products'} in high-demand regions",
                f"Review inventory in {low_demand_regions[0].get('region') if low_demand_regions else 'low-demand areas'}",
                "Analyze competitor pricing for underperforming products"
            ],
            "monthlyGoals": [
                f"Increase production of {top_products[0][0] if top_products else 'top products'} by 20%",
                "Launch promotional campaigns in 3 new regions",
                "Reduce excess inventory by 15%"
            ]
        }
        
        return jsonify({
            "status": "success",
            "message": "AI production planning insights generated successfully",
            "data": {
                "aiInsights": ai_insights,
                "demandForecast": demand_forecast,
                "stockRecommendations": stock_recommendations,
                "productionPriorities": production_priorities,
                "marketingInsights": marketing_insights,
                "promotions": promotions,
                "summaryCards": summary_cards,
                "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "analyst": current_user.get("username") if isinstance(current_user, dict) else getattr(current_user, "username", "Unknown")
            }
        }), 200
        
    except Exception as e:
        print("Error in /ai-production-planning:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to generate production planning insights.",
            "error": str(e)
        }), 500


def _generate_planning_ai_insights(heatmap_points, summary, high_demand, medium_demand, low_demand, top_products, low_products):
    """Generate AI insights for production planning using Gemini."""
    try:
        if not ai_provider:
            return {
                "summary": "AI provider not configured. Using rule-based analysis.",
                "keyFindings": [
                    f"Identified {len(high_demand)} high-demand regions requiring immediate attention",
                    f"Top product: {top_products[0][0] if top_products else 'N/A'} with highest sales",
                    f"{len(low_demand)} regions show declining demand - promotional intervention recommended"
                ],
                "strategicRecommendations": [
                    "Focus production resources on high-demand regions",
                    "Implement targeted marketing in underperforming areas",
                    "Consider seasonal adjustments for low-performing products"
                ]
            }
        
        # Build context for AI
        high_demand_info = ", ".join([f"{r.get('region')} (₹{r.get('sales', 0):,.0f})" for r in high_demand[:5]])
        low_demand_info = ", ".join([f"{r.get('region')} (₹{r.get('sales', 0):,.0f})" for r in low_demand[:3]])
        top_products_info = ", ".join([f"{p[0]} (₹{p[1]:,.0f})" for p in top_products])
        
        prompt = f"""You are an AI production planning advisor for a textile distribution company.
        
Analyze this regional demand data and provide strategic insights:

SUMMARY:
- Total Sales: ₹{summary.get('totalSales', 0):,.2f}
- Total Regions: {summary.get('totalRegions', 0)}
- High Demand Regions: {summary.get('highDemandRegions', 0)}
- Medium Demand Regions: {summary.get('mediumDemandRegions', 0)}
- Low Demand Regions: {summary.get('lowDemandRegions', 0)}

HIGH DEMAND REGIONS: {high_demand_info}
LOW DEMAND REGIONS: {low_demand_info}
TOP PRODUCTS BY SALES: {top_products_info}

Provide:
1. A 2-3 sentence executive summary of the demand landscape
2. 3 key findings from the data
3. 3 strategic recommendations for production and marketing

Format your response as:
SUMMARY: [your summary]
KEY FINDINGS:
- [finding 1]
- [finding 2]
- [finding 3]
RECOMMENDATIONS:
- [recommendation 1]
- [recommendation 2]
- [recommendation 3]
"""
        
        result = ai_provider.generate_text(prompt)
        
        if result:
            # Parse the AI response
            lines = result.strip().split('\n')
            summary_text = ""
            findings = []
            recommendations = []
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("SUMMARY:"):
                    current_section = "summary"
                    summary_text = line.replace("SUMMARY:", "").strip()
                elif line.startswith("KEY FINDINGS:"):
                    current_section = "findings"
                elif line.startswith("RECOMMENDATIONS:"):
                    current_section = "recommendations"
                elif line.startswith("- ") or line.startswith("• "):
                    content = line[2:].strip()
                    if current_section == "findings":
                        findings.append(content)
                    elif current_section == "recommendations":
                        recommendations.append(content)
                elif current_section == "summary" and line:
                    summary_text += " " + line
            
            return {
                "summary": summary_text or "Analysis complete. See findings and recommendations below.",
                "keyFindings": findings if findings else [
                    f"Identified {len(high_demand)} high-demand regions",
                    f"Top product: {top_products[0][0] if top_products else 'N/A'}",
                    f"{len(low_demand)} regions need promotional attention"
                ],
                "strategicRecommendations": recommendations if recommendations else [
                    "Increase production for high-demand products",
                    "Launch targeted campaigns in underperforming regions",
                    "Optimize inventory distribution based on demand patterns"
                ]
            }
        else:
            raise Exception("Empty AI response")
            
    except Exception as e:
        print(f"[AI Planning Insights Error]: {e}")
        return {
            "summary": f"Based on analysis of {summary.get('totalRegions', 0)} regions with total sales of ₹{summary.get('totalSales', 0):,.2f}, strategic production adjustments are recommended.",
            "keyFindings": [
                f"High demand in {len(high_demand)} regions - prioritize stock replenishment",
                f"Top performing product: {top_products[0][0] if top_products else 'N/A'}",
                f"{len(low_demand)} underperforming regions identified for marketing focus"
            ],
            "strategicRecommendations": [
                "Allocate 60% of production capacity to high-demand regions",
                "Implement promotional campaigns in low-demand areas",
                "Review and adjust pricing strategy for underperforming products"
            ]
        }


# POST: AI-Powered Stock Planning from Database Stock Heatmap Data
@distributor_bp.route("/ai-stock-planning", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
@performance_monitor
def ai_stock_planning(current_user):
    """
    Generate comprehensive AI-powered stock planning insights from database data.
    Uses the stock heatmap data to provide:
    - Stock health analysis
    - Replenishment recommendations
    - Supply priority matrix
    - Shop-specific insights
    - Promotional suggestions for slow-moving inventory
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        heatmap_points = data.get('heatmapPoints', [])
        summary = data.get('summary', {})
        
        if not heatmap_points:
            return jsonify({"status": "error", "message": "No stock data provided"}), 400
        
        # Extract key metrics from stock heatmap data
        total_shops = summary.get('totalShops', 0)
        critical_shops = summary.get('criticalStockShops', 0)
        low_shops = summary.get('lowStockShops', 0)
        healthy_shops = summary.get('healthyStockShops', 0)
        total_products = summary.get('totalProducts', 0)
        total_stock_value = summary.get('totalStockValue', 0)
        
        # Analyze shops by stock level
        critical_stock_shops = [p for p in heatmap_points if p.get('stockLevel') == 'critical']
        low_stock_shops = [p for p in heatmap_points if p.get('stockLevel') == 'low']
        healthy_stock_shops = [p for p in heatmap_points if p.get('stockLevel') == 'healthy']
        
        # Get products needing attention across all shops
        products_needing_attention = []
        for shop in heatmap_points:
            for item in shop.get('stockDetails', []):
                if item.get('status') in ['critical', 'low']:
                    products_needing_attention.append({
                        'shop': shop.get('shopName'),
                        'shopId': shop.get('shopId'),
                        'region': shop.get('region'),
                        **item
                    })
        
        # Sort by stock ratio (lowest first)
        products_needing_attention.sort(key=lambda x: x.get('stock_ratio', 1))
        
        # Generate AI insights
        ai_insights = _generate_stock_ai_insights(
            heatmap_points, summary, critical_stock_shops,
            low_stock_shops, healthy_stock_shops, products_needing_attention
        )
        
        # Build stock forecast (based on current levels and safety stock gaps)
        stock_forecast = []
        for shop in sorted(heatmap_points, key=lambda x: x.get('healthScore', 1)):
            critical_items = shop.get('criticalItems', 0)
            low_items = shop.get('lowItems', 0)
            
            if critical_items > 0:
                urgency = 'critical'
                days_until_stockout = 3  # Estimate
            elif low_items > 0:
                urgency = 'warning'
                days_until_stockout = 10
            else:
                urgency = 'healthy'
                days_until_stockout = 30
            
            stock_forecast.append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "currentStock": shop.get('totalStock', 0),
                "stockValue": shop.get('stockValue', 0),
                "criticalItems": critical_items,
                "lowItems": low_items,
                "healthyItems": shop.get('healthyItems', 0),
                "healthScore": shop.get('healthScore', 0),
                "urgency": urgency,
                "estimatedDaysUntilStockout": days_until_stockout,
                "topProduct": shop.get('topProduct', 'N/A')
            })
        
        # Build replenishment recommendations
        stock_recommendations = []
        for shop in sorted(heatmap_points, key=lambda x: x.get('healthScore', 1)):
            stock_level = shop.get('stockLevel')
            
            if stock_level == 'critical':
                priority = 'urgent'
                action = 'Immediate restocking required - multiple items below safety stock'
                timeline = '1-2 days'
            elif stock_level == 'low':
                priority = 'high'
                action = 'Schedule restocking this week - some items approaching safety stock'
                timeline = '3-5 days'
            else:
                priority = 'normal'
                action = 'Monitor inventory levels - stock health is good'
                timeline = '1-2 weeks'
            
            # Calculate recommended restock quantities
            restock_items = []
            for item in shop.get('stockDetails', []):
                if item.get('status') in ['critical', 'low']:
                    # Recommend restocking to 150% of safety stock
                    safety = item.get('safety_stock', 0)
                    current = item.get('qty_available', 0)
                    recommended = max(0, int(safety * 1.5) - current)
                    if recommended > 0:
                        restock_items.append({
                            'product': item.get('product_name'),
                            'category': item.get('category'),
                            'current': current,
                            'safety': safety,
                            'recommended': recommended,
                            'estimatedCost': round(recommended * item.get('price', 0), 2)
                        })
            
            stock_recommendations.append({
                "shop": shop.get('shopName'),
                "shopId": shop.get('shopId'),
                "region": shop.get('region'),
                "stockLevel": stock_level,
                "priority": priority,
                "action": action,
                "timeline": timeline,
                "restockItems": restock_items[:5],  # Top 5 items to restock
                "totalRestockValue": sum(i['estimatedCost'] for i in restock_items)
            })
        
        # Build supply priority matrix
        supply_priorities = {
            "urgent": [],
            "high": [],
            "normal": []
        }
        
        for shop in critical_stock_shops[:5]:
            supply_priorities["urgent"].append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "criticalItems": shop.get('criticalItems', 0),
                "reason": f"Critical stock levels - {shop.get('criticalItems', 0)} items below 50% of safety stock"
            })
        
        for shop in low_stock_shops[:5]:
            supply_priorities["high"].append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "lowItems": shop.get('lowItems', 0),
                "reason": f"Low stock warning - {shop.get('lowItems', 0)} items approaching safety stock"
            })
        
        for shop in healthy_stock_shops[:3]:
            supply_priorities["normal"].append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "healthyItems": shop.get('healthyItems', 0),
                "reason": "Stock levels healthy - schedule routine restocking"
            })
        
        # Build shop-specific marketing insights
        marketing_insights = []
        for shop in critical_stock_shops[:3]:
            marketing_insights.append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "insight": "Stock running low - pause promotional campaigns until restocked",
                "recommendedAction": "Focus on restocking before new promotions",
                "priority": "high"
            })
        
        for shop in healthy_stock_shops[:3]:
            marketing_insights.append({
                "shop": shop.get('shopName'),
                "region": shop.get('region'),
                "insight": "Good stock levels - ideal for promotional campaigns",
                "recommendedAction": f"Launch promotions for {shop.get('topProduct', 'top products')}",
                "priority": "medium"
            })
        
        # Build promotion suggestions
        promotions = []
        
        # Clear slow-moving inventory
        if products_needing_attention:
            overstocked_items = [p for p in products_needing_attention if p.get('stock_ratio', 0) > 2]
            if overstocked_items:
                promotions.append({
                    "type": "clearance",
                    "title": "Clear Excess Inventory",
                    "description": "Offer discounts on overstocked items to improve cash flow",
                    "targetShops": list(set([p.get('shop') for p in overstocked_items[:5]])),
                    "expectedROI": "15-25%",
                    "duration": "1 week"
                })
        
        # Push sales in healthy shops
        if healthy_stock_shops:
            promotions.append({
                "type": "promotion",
                "title": "Stock-Ready Sales Push",
                "description": "Launch promotional campaigns in well-stocked shops",
                "targetShops": [s.get('shopName') for s in healthy_stock_shops[:3]],
                "expectedROI": "20-30%",
                "duration": "2 weeks"
            })
        
        # Build summary cards data
        total_restock_value = sum(r['totalRestockValue'] for r in stock_recommendations)
        
        summary_cards = {
            "totalStockValue": round(total_stock_value, 2),
            "totalRestockNeeded": round(total_restock_value, 2),
            "urgentShops": len(critical_stock_shops),
            "warningShops": len(low_stock_shops),
            "healthyShops": len(healthy_stock_shops),
            "weeklyTasks": [
                f"Restock {critical_stock_shops[0].get('shopName') if critical_stock_shops else 'critical shops'} immediately",
                f"Review {len(products_needing_attention)} products needing attention",
                "Update safety stock levels based on demand patterns"
            ],
            "monthlyGoals": [
                "Reduce critical stock situations by 50%",
                "Optimize safety stock levels across all shops",
                "Improve average stock health score to 0.8+"
            ]
        }
        
        return jsonify({
            "status": "success",
            "message": "AI stock planning insights generated successfully",
            "data": {
                "aiInsights": ai_insights,
                "stockForecast": stock_forecast,
                "stockRecommendations": stock_recommendations,
                "supplyPriorities": supply_priorities,
                "marketingInsights": marketing_insights,
                "promotions": promotions,
                "summaryCards": summary_cards,
                "productsNeedingAttention": products_needing_attention[:20],
                "generatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "analyst": current_user.get("username") if isinstance(current_user, dict) else getattr(current_user, "username", "Unknown")
            }
        }), 200
        
    except Exception as e:
        print("Error in /ai-stock-planning:", e)
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Failed to generate stock planning insights.",
            "error": str(e)
        }), 500


def _generate_stock_ai_insights(heatmap_points, summary, critical_shops, low_shops, healthy_shops, products_needing_attention):
    """Generate AI insights for stock planning using Gemini with product-level detail."""
    try:
        # Extract product-level details for richer insights
        critical_products_list = []
        low_products_list = []
        category_issues = {}
        
        for shop in heatmap_points:
            for product in shop.get('stockDetails', []):
                if product.get('status') == 'critical':
                    critical_products_list.append({
                        'name': product.get('product_name'),
                        'category': product.get('category'),
                        'shop': shop.get('shopName'),
                        'qty': product.get('qty_available'),
                        'safety': product.get('safety_stock'),
                        'sold': product.get('total_sold', 0)
                    })
                    cat = product.get('category', 'Unknown')
                    category_issues[cat] = category_issues.get(cat, 0) + 1
                elif product.get('status') == 'low':
                    low_products_list.append({
                        'name': product.get('product_name'),
                        'category': product.get('category'),
                        'shop': shop.get('shopName'),
                        'qty': product.get('qty_available'),
                        'safety': product.get('safety_stock'),
                        'sold': product.get('total_sold', 0)
                    })
        
        # Sort by most critical (lowest stock)
        critical_products_list.sort(key=lambda x: x.get('qty', 0))
        
        # Get top 5 most critical products
        top_critical = critical_products_list[:5]
        
        # Find high-selling products that are critical (based on units sold, not revenue)
        high_selling_critical = sorted(
            [p for p in critical_products_list if p.get('sold', 0) > 0],
            key=lambda x: x.get('sold', 0),
            reverse=True
        )[:3]
        
        if not ai_provider:
            print("[AI Stock Planning] AI provider not configured, using rule-based analysis")
            # Enhanced rule-based response with product names
            critical_product_names = [p['name'] for p in top_critical[:3]]
            return {
                "summary": f"Inventory health requires attention. {len(critical_products_list)} products at critical levels across {len(critical_shops)} shops. Priority restocking needed for {', '.join(critical_product_names) if critical_product_names else 'multiple items'}.",
                "keyFindings": [
                    f"**Critical Products:** {', '.join([p['name'] for p in top_critical[:3]])} are at dangerously low stock levels" if top_critical else "No critical products identified",
                    f"**High-Demand Alert:** {', '.join([p['name'] for p in high_selling_critical])} are fast-selling products running low" if high_selling_critical else f"{len(low_products_list)} products approaching reorder point",
                    f"**Category Alert:** {max(category_issues.items(), key=lambda x: x[1])[0] if category_issues else 'Multiple categories'} has the most stock issues ({max(category_issues.values()) if category_issues else 0} products)"
                ],
                "strategicRecommendations": [
                    f"**Urgent:** Restock {top_critical[0]['name']} at {top_critical[0]['shop']} immediately - only {top_critical[0]['qty']} units remaining" if top_critical else "Review all critical stock items",
                    f"**Priority:** Focus on {max(category_issues.items(), key=lambda x: x[1])[0] if category_issues else 'low-stock'} category - accounts for majority of stock issues",
                    "**Process:** Implement daily stock monitoring for products with sell-through rate above 70%"
                ]
            }
        
        # Build detailed context for AI with product specifics (no revenue - privacy)
        critical_details = "\n".join([
            f"  - {p['name']} ({p['category']}) at {p['shop']}: {p['qty']} units left (safety: {p['safety']}), sold {p['sold']} units"
            for p in top_critical
        ])
        
        high_selling_details = "\n".join([
            f"  - {p['name']}: {p['sold']} units sold but only {p['qty']} units remaining"
            for p in high_selling_critical
        ]) if high_selling_critical else "None identified"
        
        category_breakdown = "\n".join([
            f"  - {cat}: {count} products with stock issues"
            for cat, count in sorted(category_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        ]) if category_issues else "No category breakdown available"
        
        prompt = f"""You are an AI inventory planning advisor for a textile distribution company.
        
Analyze this detailed stock data and provide specific, actionable insights:

OVERALL SUMMARY:
- Total Shops: {summary.get('totalShops', 0)}
- Critical Stock Shops: {summary.get('criticalStockShops', 0)}
- Low Stock Shops: {summary.get('lowStockShops', 0)}
- Healthy Stock Shops: {summary.get('healthyStockShops', 0)}
- Total Products: {summary.get('totalProducts', 0)}
- Total Stock Value: ₹{summary.get('totalStockValue', 0):,.2f}
- Critical Products Count: {len(critical_products_list)}
- Low Stock Products Count: {len(low_products_list)}

TOP 5 MOST CRITICAL PRODUCTS (need immediate restocking):
{critical_details or 'No critical products'}

HIGH-DEMAND PRODUCTS AT RISK (fast-selling items running low):
{high_selling_details}

CATEGORY BREAKDOWN OF STOCK ISSUES:
{category_breakdown}

Based on this data, provide:
1. A 2-3 sentence executive summary mentioning specific product names and shops
2. 3 key findings - BE SPECIFIC with product names, shops, and numbers
3. 3 strategic recommendations - INCLUDE specific product names and actionable steps

Use **bold** for emphasis on product names and key metrics.

Format your response as:
SUMMARY: [your summary with specific product names]
KEY FINDINGS:
- [finding 1 with specific product/shop names]
- [finding 2 with specific product/shop names]
- [finding 3 with specific product/shop names]
RECOMMENDATIONS:
- [recommendation 1 with specific actions]
- [recommendation 2 with specific actions]
- [recommendation 3 with specific actions]
"""
        
        print("[AI Stock Planning] Calling AI API with enhanced product details...")
        result = ai_provider.generate_text(prompt, timeout=120)
        print("[AI Stock Planning] AI API response received")
        
        if result:
            # Parse the AI response
            lines = result.strip().split('\n')
            summary_text = ""
            findings = []
            recommendations = []
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("SUMMARY:"):
                    current_section = "summary"
                    summary_text = line.replace("SUMMARY:", "").strip()
                elif line.startswith("KEY FINDINGS:"):
                    current_section = "findings"
                elif line.startswith("RECOMMENDATIONS:"):
                    current_section = "recommendations"
                elif line.startswith("- ") or line.startswith("• "):
                    content = line[2:].strip()
                    if current_section == "findings":
                        findings.append(content)
                    elif current_section == "recommendations":
                        recommendations.append(content)
                elif current_section == "summary" and line:
                    summary_text += " " + line
            
            # Fallback if parsing failed
            if not summary_text and not findings:
                # Return the raw result if structured parsing failed
                return {
                    "summary": result[:500] if len(result) > 500 else result,
                    "keyFindings": [
                        f"Critical: {len(critical_products_list)} products need immediate restocking",
                        f"At Risk: Fast-selling products like {high_selling_critical[0]['name'] if high_selling_critical else 'several items'} are running low",
                        f"Category Focus: {max(category_issues.items(), key=lambda x: x[1])[0] if category_issues else 'Multiple categories'} needs attention"
                    ],
                    "strategicRecommendations": [
                        f"Restock {top_critical[0]['name']} at {top_critical[0]['shop']} within 24 hours" if top_critical else "Review all critical items",
                        "Prioritize fast-selling products to maintain availability",
                        "Set up automated alerts for products below 75% safety stock"
                    ]
                }
            
            return {
                "summary": summary_text or f"Analysis of {summary.get('totalShops', 0)} shops reveals {len(critical_products_list)} critical products requiring immediate attention.",
                "keyFindings": findings if findings else [
                    f"**{top_critical[0]['name']}** at {top_critical[0]['shop']} is most critical with only {top_critical[0]['qty']} units" if top_critical else "Multiple products at low levels",
                    f"**{len(critical_products_list)}** products across **{len(critical_shops)}** shops need immediate restocking",
                    f"**{max(category_issues.items(), key=lambda x: x[1])[0] if category_issues else 'Various categories'}** category has the most stock issues"
                ],
                "strategicRecommendations": recommendations if recommendations else [
                    f"Restock **{top_critical[0]['name']}** at **{top_critical[0]['shop']}** immediately" if top_critical else "Review all critical stock items",
                    "Focus on fast-selling products to maintain stock availability",
                    "Implement daily monitoring for fast-moving inventory"
                ]
            }
        else:
            raise Exception("Empty AI response")
            
    except Exception as e:
        print(f"[AI Stock Insights Error]: {e}")
        # Provide product-specific fallback
        top_critical = []
        for shop in heatmap_points:
            for product in shop.get('stockDetails', []):
                if product.get('status') == 'critical':
                    top_critical.append({
                        'name': product.get('product_name'),
                        'shop': shop.get('shopName'),
                        'qty': product.get('qty_available')
                    })
        top_critical.sort(key=lambda x: x.get('qty', 0))
        
        return {
            "summary": f"Stock analysis for {summary.get('totalShops', 0)} shops complete. {summary.get('criticalStockShops', 0)} shops have critical stock levels with {len(top_critical)} products needing immediate attention.",
            "keyFindings": [
                f"**Most Critical:** {top_critical[0]['name']} at {top_critical[0]['shop']} has only {top_critical[0]['qty']} units" if top_critical else "Multiple products at critically low levels",
                f"**Shop Alert:** {len(critical_shops)} shops require immediate restocking attention",
                f"**Low Stock Warning:** {len(low_shops)} additional shops approaching reorder points"
            ],
            "strategicRecommendations": [
                f"**Priority 1:** Restock {top_critical[0]['name']} within 24 hours" if top_critical else "Review all critical inventory",
                "**Priority 2:** Schedule restocking for all shops with low stock warnings this week",
                "**Process:** Consider safety stock adjustments for frequently depleted items"
            ]
        }


# =============================================================================
# AI DEMAND FORECAST ENDPOINT
# =============================================================================
@distributor_bp.route("/ai-demand-forecast", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
def ai_demand_forecast(current_user):
    """
    AI-powered demand forecasting for distributor's products.
    Uses historical sales data to predict demand for next 14 days.
    """
    try:
        distributor_id = current_user['id']
        data = request.get_json() or {}
        
        # Get products supplied by this distributor with their sales history (units only, not revenue)
        products_with_sales = db.session.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Shop.name.label('shop_name'),
            Inventory.qty_available,
            Inventory.safety_stock,
            func.coalesce(func.sum(SalesData.quantity_sold), 0).label('total_sold'),
            func.count(SalesData.id).label('sales_records')
        ).join(
            DistributorSupply, DistributorSupply.product_id == Product.id
        ).join(
            Shop, Shop.id == DistributorSupply.shop_id
        ).outerjoin(
            Inventory, Inventory.product_id == Product.id
        ).outerjoin(
            SalesData, SalesData.product_id == Product.id
        ).filter(
            DistributorSupply.distributor_id == distributor_id
        ).group_by(
            Product.id, Product.name, Product.category, Product.price,
            Shop.name, Inventory.qty_available, Inventory.safety_stock
        ).all()
        
        if not products_with_sales:
            return jsonify({
                "status": "success",
                "data": {
                    "forecasts": [],
                    "aiAnalysis": "No products found for this distributor."
                }
            })
        
        # Calculate demand forecast for each product
        forecasts = []
        for product in products_with_sales:
            # Calculate average daily sales (assuming 30 days of data)
            days_of_data = max(product.sales_records, 1)
            avg_daily_sales = product.total_sold / max(days_of_data, 30) if product.total_sold > 0 else 0
            
            # Predict demand for next 14 days
            predicted_demand_14d = round(avg_daily_sales * 14, 0)
            
            # Calculate days until stockout
            current_stock = product.qty_available or 0
            days_until_stockout = round(current_stock / avg_daily_sales, 1) if avg_daily_sales > 0 else 999
            
            # Determine action needed
            if current_stock < predicted_demand_14d * 0.5:
                action = "ORDER NOW"
                action_class = "critical"
            elif current_stock < predicted_demand_14d:
                action = "RESTOCK SOON"
                action_class = "warning"
            else:
                action = "ADEQUATE"
                action_class = "healthy"
            
            forecasts.append({
                "productId": product.id,
                "productName": product.name,
                "category": product.category,
                "shopName": product.shop_name,
                "currentStock": current_stock,
                "predictedDemand14d": int(predicted_demand_14d),
                "avgDailySales": round(avg_daily_sales, 1),
                "daysUntilStockout": days_until_stockout if days_until_stockout < 999 else None,
                "action": action,
                "actionClass": action_class,
                "totalSold": product.total_sold
            })
        
        # Sort by urgency (critical first)
        action_priority = {"ORDER NOW": 0, "RESTOCK SOON": 1, "ADEQUATE": 2}
        forecasts.sort(key=lambda x: (action_priority.get(x["action"], 3), -x["predictedDemand14d"]))
        
        # Count categories
        critical_products = [f for f in forecasts if f["action"] == "ORDER NOW"]
        warning_products = [f for f in forecasts if f["action"] == "RESTOCK SOON"]
        
        # Generate smart summary WITHOUT calling AI (instant response)
        # This avoids API bottlenecks when multiple AI endpoints are called simultaneously
        if critical_products:
            top_critical = critical_products[:3]
            product_names = ", ".join([f"**{p['productName']}**" for p in top_critical])
            ai_analysis = f"{product_names} face the highest stockout risk with less than 50% of predicted 14-day demand in stock. Prioritize restocking these {len(critical_products)} critical items immediately, focusing on products with highest daily sales velocity."
        elif warning_products:
            ai_analysis = f"No critical stockouts detected. {len(warning_products)} products need restocking soon to meet upcoming demand. Monitor products approaching safety stock levels."
        else:
            ai_analysis = "All products have adequate stock levels to meet predicted 14-day demand. Continue monitoring sales velocity for any sudden changes."
        
        return jsonify({
            "status": "success",
            "data": {
                "forecasts": forecasts,  # Return all forecasts
                "summary": {
                    "totalProducts": len(forecasts),
                    "criticalCount": len(critical_products),
                    "warningCount": len(warning_products),
                    "healthyCount": len([f for f in forecasts if f["action"] == "ADEQUATE"])
                },
                "aiAnalysis": ai_analysis
            }
        })
        
    except Exception as e:
        print(f"[AI Demand Forecast Error]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================================================================
# AI REVENUE IMPACT ENDPOINT
# =============================================================================
# AI STOCK IMPACT ENDPOINT (Privacy-Respecting - Units Based)
# =============================================================================
@distributor_bp.route("/ai-revenue-impact", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
def ai_stock_impact(current_user):
    """
    AI-powered stock impact analysis for supply decisions.
    Shows potential sales loss from stockouts and gains from restocking.
    Uses UNITS SOLD (not revenue) to respect shop owner privacy.
    """
    try:
        distributor_id = current_user['id']
        
        # Get products with sales and inventory data (no revenue - privacy)
        products_data = db.session.query(
            Product.id,
            Product.name,
            Product.category,
            Product.price,
            Shop.name.label('shop_name'),
            Inventory.qty_available,
            Inventory.safety_stock,
            func.coalesce(func.sum(SalesData.quantity_sold), 0).label('total_sold'),
            func.count(SalesData.id).label('sales_records')
        ).join(
            DistributorSupply, DistributorSupply.product_id == Product.id
        ).join(
            Shop, Shop.id == DistributorSupply.shop_id
        ).outerjoin(
            Inventory, Inventory.product_id == Product.id
        ).outerjoin(
            SalesData, SalesData.product_id == Product.id
        ).filter(
            DistributorSupply.distributor_id == distributor_id
        ).group_by(
            Product.id, Product.name, Product.category, Product.price,
            Shop.name, Inventory.qty_available, Inventory.safety_stock
        ).all()
        
        if not products_data:
            return jsonify({
                "status": "success",
                "data": {
                    "stockImpacts": [],
                    "summary": {},
                    "aiAnalysis": "No products found."
                }
            })
        
        stock_impacts = []
        total_units_at_risk = 0
        total_restock_needed = 0
        
        for product in products_data:
            current_stock = product.qty_available or 0
            safety_stock = product.safety_stock or 10
            total_sold = product.total_sold or 0
            sales_records = product.sales_records or 0
            
            # Calculate average daily sales (estimate from records)
            avg_daily_sales = total_sold / max(sales_records, 30) if total_sold > 0 else 0
            
            # Calculate stock ratio
            stock_ratio = current_stock / safety_stock if safety_stock > 0 else 1
            
            # Calculate units at risk (if stock runs out)
            if stock_ratio < 0.5:  # Critical
                # Estimate potential lost sales = units below safety stock
                units_at_risk = max(0, safety_stock - current_stock)
                status = "critical"
            elif stock_ratio < 1.0:  # Low
                units_at_risk = max(0, int((safety_stock - current_stock) * 0.5))
                status = "warning"
            else:
                units_at_risk = 0
                status = "healthy"
            
            # Calculate restock quantity needed
            restock_qty = max(0, int(safety_stock * 1.5) - current_stock)
            
            total_units_at_risk += units_at_risk
            total_restock_needed += restock_qty
            
            stock_impacts.append({
                "productId": product.id,
                "productName": product.name,
                "category": product.category,
                "shopName": product.shop_name,
                "currentStock": current_stock,
                "safetyStock": safety_stock,
                "stockRatio": round(stock_ratio * 100, 1),
                "totalSold": total_sold,
                "avgDailySales": round(avg_daily_sales, 1),
                "unitsAtRisk": units_at_risk,
                "restockQty": restock_qty,
                "status": status
            })
        
        # Sort by units at risk (highest first)
        stock_impacts.sort(key=lambda x: (-x["unitsAtRisk"], -x["totalSold"]))
        
        # Count by status
        critical_products = [r for r in stock_impacts if r["status"] == "critical"]
        warning_products = [r for r in stock_impacts if r["status"] == "warning"]
        
        # Generate smart summary WITHOUT calling AI (instant response)
        if critical_products:
            top_critical = critical_products[:3]
            product_names = ", ".join([f"**{p['productName']}**" for p in top_critical])
            ai_analysis = f"{product_names} have the highest stockout risk with **{total_units_at_risk} units** at risk. Prioritize restocking these {len(critical_products)} critical items immediately - they need **{total_restock_needed} units** total to reach safe stock levels."
        elif warning_products:
            ai_analysis = f"No critical stockouts, but {len(warning_products)} products are running low. Total of **{total_restock_needed} units** recommended for restocking to maintain healthy inventory levels."
        else:
            ai_analysis = "All products are at healthy stock levels. No immediate restocking required. Continue monitoring for demand changes."
        
        return jsonify({
            "status": "success",
            "data": {
                "stockImpacts": stock_impacts,  # Return all stock impacts
                "summary": {
                    "totalUnitsAtRisk": total_units_at_risk,
                    "totalRestockNeeded": total_restock_needed,
                    "criticalProducts": len(critical_products),
                    "warningProducts": len(warning_products)
                },
                "aiAnalysis": ai_analysis
            }
        })
        
    except Exception as e:
        print(f"[AI Revenue Impact Error]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================================================================
# AI CHAT ASSISTANT ENDPOINT
# =============================================================================
@distributor_bp.route("/ai-chat", methods=["POST"])
@token_required
@roles_required('distributor', 'manufacturer')
def ai_chat_assistant(current_user):
    """
    AI-powered chat assistant for inventory and planning questions.
    Answers natural language questions about stock, demand, and recommendations.
    Now accepts pre-loaded AI insights context for richer answers.
    """
    try:
        distributor_id = current_user['id']
        data = request.get_json() or {}
        
        user_message = data.get("message", "").strip()
        frontend_context = data.get("context")  # Pre-loaded AI insights from frontend
        
        if not user_message:
            return jsonify({
                "status": "error",
                "message": "Please provide a message"
            }), 400
        
        # Build context - use frontend context if available (richer data)
        if frontend_context:
            # Use the pre-computed AI insights for better answers
            context = build_rich_context(frontend_context)
        else:
            # Fallback to basic database query
            context = build_basic_context(distributor_id)
        
        # Build prompt for AI
        prompt = f"""You are an AI inventory assistant for a textile distributor. Answer the user's question based on their inventory data.

{context}

USER QUESTION: {user_message}

Provide a helpful, specific, and actionable response. If the question is about:
- Restocking: Give specific product names, quantities, and priority order based on demand forecasts
- Stockouts: Reference days until stockout and urgency levels
- Trends: Analyze the sales patterns and predicted demand shown
- General advice: Be specific to their actual inventory situation

Keep responses concise (2-4 sentences) and use **bold** for emphasis on key figures and recommendations.
If the question is unclear or unrelated to inventory, politely redirect to inventory-related topics."""

        ai_provider = get_provider()
        
        try:
            ai_response = ai_provider.generate_text(prompt, timeout=60)
        except Exception as e:
            print(f"[AI Chat] Error: {e}")
            ai_response = "I apologize, I'm having trouble processing your request. Please try again or ask a simpler question about your inventory."
        
        return jsonify({
            "status": "success",
            "data": {
                "response": ai_response
            }
        })
        
    except Exception as e:
        print(f"[AI Chat Error]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def build_rich_context(frontend_context):
    """Build rich context from pre-loaded AI insights."""
    context_parts = []
    
    # Stock Planning Summary
    if frontend_context.get('stockPlanning'):
        sp = frontend_context['stockPlanning']
        if sp.get('summary'):
            context_parts.append(f"""
STOCK PLANNING SUMMARY:
- Total Products Monitored: {sp['summary'].get('totalProducts', 'N/A')}
- Critical Stock Items: {sp['summary'].get('criticalCount', 0)}
- Low Stock Items: {sp['summary'].get('lowCount', 0)}
- Healthy Stock Items: {sp['summary'].get('healthyCount', 0)}
""")
        if sp.get('aiInsights', {}).get('keyFindings'):
            context_parts.append("KEY FINDINGS:\n" + "\n".join([f"- {f}" for f in sp['aiInsights']['keyFindings'][:5]]))
    
    # Demand Forecast Data - Include ALL products
    if frontend_context.get('demandForecast'):
        df = frontend_context['demandForecast']
        
        if df.get('summary'):
            context_parts.append(f"\nDEMAND FORECAST SUMMARY:")
            context_parts.append(f"- Total Products Analyzed: {df['summary'].get('totalProducts', 0)}")
            context_parts.append(f"- Products needing immediate order (ORDER NOW): {df['summary'].get('criticalCount', 0)}")
            context_parts.append(f"- Products to restock soon: {df['summary'].get('warningCount', 0)}")
            context_parts.append(f"- Products with adequate stock: {df['summary'].get('healthyCount', 0)}")
        
        if df.get('forecasts'):
            # Include ALL ORDER NOW items
            order_now_items = [f for f in df['forecasts'] if f.get('action') == 'ORDER NOW']
            if order_now_items:
                context_parts.append(f"\nALL PRODUCTS NEEDING IMMEDIATE ORDER ({len(order_now_items)} items):")
                for item in order_now_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('currentStock', 0)} in stock, predicted demand {item.get('predictedDemand14d', 0)} units, stockout in {item.get('daysUntilStockout', 'N/A')} days, avg {item.get('avgDailySales', 0)}/day")
            
            # Include ALL RESTOCK SOON items
            restock_soon_items = [f for f in df['forecasts'] if f.get('action') == 'RESTOCK SOON']
            if restock_soon_items:
                context_parts.append(f"\nALL PRODUCTS TO RESTOCK SOON ({len(restock_soon_items)} items):")
                for item in restock_soon_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('currentStock', 0)} in stock, predicted demand {item.get('predictedDemand14d', 0)} units, stockout in {item.get('daysUntilStockout', 'N/A')} days")
            
            # Include ALL ADEQUATE items (for complete picture)
            adequate_items = [f for f in df['forecasts'] if f.get('action') == 'ADEQUATE']
            if adequate_items:
                context_parts.append(f"\nPRODUCTS WITH ADEQUATE STOCK ({len(adequate_items)} items):")
                for item in adequate_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('currentStock', 0)} in stock")
    
    # Stock Impact Data - Include ALL products
    if frontend_context.get('stockImpact'):
        si = frontend_context['stockImpact']
        if si.get('summary'):
            context_parts.append(f"\nSTOCK IMPACT ANALYSIS:")
            context_parts.append(f"- Critical Products: {si['summary'].get('criticalProducts', 0)}")
            context_parts.append(f"- Low Stock Products: {si['summary'].get('warningProducts', 0)}")
            context_parts.append(f"- Total Units at Risk: {si['summary'].get('totalUnitsAtRisk', 0)}")
            context_parts.append(f"- Total Restock Needed: {si['summary'].get('totalRestockNeeded', 0)} units")
        
        if si.get('stockImpacts'):
            # Group by status
            critical_items = [item for item in si['stockImpacts'] if item.get('status') == 'critical']
            low_items = [item for item in si['stockImpacts'] if item.get('status') == 'low']
            healthy_items = [item for item in si['stockImpacts'] if item.get('status') == 'healthy']
            
            if critical_items:
                context_parts.append(f"\nALL CRITICAL STOCK PRODUCTS ({len(critical_items)} items):")
                for item in critical_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('stockRatio', 0)}% stock level, {item.get('unitsAtRisk', 0)} units at risk, restock {item.get('restockQty', 0)} units, sold {item.get('totalSold', 0)} units")
            
            if low_items:
                context_parts.append(f"\nALL LOW STOCK PRODUCTS ({len(low_items)} items):")
                for item in low_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('stockRatio', 0)}% stock level, restock {item.get('restockQty', 0)} units")
            
            if healthy_items:
                context_parts.append(f"\nHEALTHY STOCK PRODUCTS ({len(healthy_items)} items):")
                for item in healthy_items:
                    context_parts.append(f"- {item.get('productName', 'Unknown')} at {item.get('shopName', 'Unknown Shop')}: {item.get('stockRatio', 0)}% stock level, sold {item.get('totalSold', 0)} units")
    
    return "\n".join(context_parts) if context_parts else "No detailed insights available."


def build_basic_context(distributor_id):
    """Build basic context from database (fallback when no frontend context)."""
    stock_status = db.session.query(
        Product.name,
        Product.category,
        Shop.name.label('shop_name'),
        Inventory.qty_available,
        Inventory.safety_stock,
        func.coalesce(func.sum(SalesData.quantity_sold), 0).label('total_sold')
    ).join(
        DistributorSupply, DistributorSupply.product_id == Product.id
    ).join(
        Shop, Shop.id == DistributorSupply.shop_id
    ).outerjoin(
        Inventory, Inventory.product_id == Product.id
    ).outerjoin(
        SalesData, SalesData.product_id == Product.id
    ).filter(
        DistributorSupply.distributor_id == distributor_id
    ).group_by(
        Product.name, Product.category, Shop.name,
        Inventory.qty_available, Inventory.safety_stock
    ).all()
    
    critical_products = []
    low_products = []
    healthy_products = []
    
    for item in stock_status:
        qty = item.qty_available or 0
        safety = item.safety_stock or 10
        ratio = qty / safety if safety > 0 else 1
        
        product_info = {
            "name": item.name,
            "category": item.category,
            "shop": item.shop_name,
            "stock": qty,
            "safety": safety,
            "sold": item.total_sold
        }
        
        if ratio < 0.5:
            critical_products.append(product_info)
        elif ratio < 1.0:
            low_products.append(product_info)
        else:
            healthy_products.append(product_info)
    
    return f"""
INVENTORY CONTEXT FOR DISTRIBUTOR:
- Total Products: {len(stock_status)}
- Critical Stock (< 50% safety): {len(critical_products)} products
- Low Stock (50-100% safety): {len(low_products)} products
- Healthy Stock (> 100% safety): {len(healthy_products)} products

CRITICAL PRODUCTS (need immediate restocking):
{chr(10).join([f"- {p['name']} at {p['shop']}: {p['stock']} units (safety: {p['safety']}), sold {p['sold']} units" for p in critical_products[:5]]) or "None"}

LOW STOCK PRODUCTS (watch list):
{chr(10).join([f"- {p['name']} at {p['shop']}: {p['stock']} units (safety: {p['safety']})" for p in low_products[:5]]) or "None"}

TOP SELLING PRODUCTS (by units sold):
{chr(10).join([f"- {p['name']}: {p['sold']} units sold" for p in sorted(critical_products + low_products + healthy_products, key=lambda x: -x['sold'])[:5]])}
"""
