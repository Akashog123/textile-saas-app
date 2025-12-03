#app.py
import os
import sys
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from models.model import db
from config import Config
from flask_migrate import Migrate

# Environment Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.insert(0, BASE_DIR)

# Gemini API Key verification
if not os.getenv("GEMINI_API_KEY"):
    print("[Warning] GEMINI_API_KEY not found in .env file.")
else:
    print("GEMINI_API_KEY loaded successfully.")

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.profile_routes import profile_bp
from routes.shop_routes import shop_bp
from routes.inventory import inventory_bp  
from routes.heatmap_routes import heatmap_bp
from routes.trending_routes import trending_shops_bp
from routes.ai_find_stores import ai_bp
from routes.top_selling_routes import top_selling_bp
from routes.image_routes import image_bp
from routes.stores_routes import stores_bp
from routes.product_routes import product_bp
from routes.inquiry import inquiry_bp
from routes.discovery_portal import discovery_portal_bp
from routes.shop_explorer import shop_explorer_bp
from routes.marketing_routes import marketing_bp
from routes.distributor_routes import distributor_bp
from routes.production_plan import production_bp
from routes.pdf_service import pdf_bp
from routes.catalog_routes import catalog_bp
from routes.nearby_search import nearby_bp
from routes.performance_routes import performance_bp 
from routes.review_routes import reviews_bp

# Flask Application Setup
app = Flask(
    __name__,
    instance_path=Config.DATA_DIR
)
app.config.from_object(Config)

# CORS Configuration
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000","http://127.0.0.1:8000" ]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)
# Security Headers Middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not app.config['DEBUG']:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Global Error Handler
@app.errorhandler(Exception)
def handle_error(error):
    """Handle all unhandled exceptions"""
    app.logger.error(f"Unhandled exception: {error}", exc_info=True)
    if app.config['DEBUG']:
        return jsonify({"status": "error", "message": str(error)}), 500
    else:
        return jsonify({"status": "error", "message": "An internal error occurred"}), 500

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
app.register_blueprint(profile_bp, url_prefix="/api/v1/profile")
app.register_blueprint(shop_bp, url_prefix="/api/v1/shop")
app.register_blueprint(inventory_bp, url_prefix="/api/v1/inventory")
app.register_blueprint(heatmap_bp, url_prefix="/api/v1/region-demand-heatmap")
app.register_blueprint(ai_bp, url_prefix="/api/v1/ai-find-stores")
app.register_blueprint(top_selling_bp, url_prefix="/api/v1/top-selling-products")
app.register_blueprint(trending_shops_bp, url_prefix="/api/v1/trending-shops")
app.register_blueprint(image_bp, url_prefix="/api/v1/compare-images")
app.register_blueprint(stores_bp, url_prefix="/api/v1/stores")
app.register_blueprint(product_bp, url_prefix="/api/v1/products")
app.register_blueprint(inquiry_bp, url_prefix="/api/v1/inquiry")
app.register_blueprint(discovery_portal_bp, url_prefix="/api/v1/customer")
app.register_blueprint(shop_explorer_bp, url_prefix="/api/v1/customer/shops")
# app.register_blueprint(shop_bp, url_prefix="/api/v1/shop/my-shops")
app.register_blueprint(marketing_bp, url_prefix="/api/v1/marketing")
app.register_blueprint(distributor_bp, url_prefix="/api/v1/distributor")
app.register_blueprint(production_bp, url_prefix="/api/v1/production")
app.register_blueprint(pdf_bp, url_prefix="/api/v1/pdf")
app.register_blueprint(catalog_bp, url_prefix="/api/v1/catalog")
app.register_blueprint(nearby_bp)
app.register_blueprint(performance_bp, url_prefix="/api/v1/performance")
app.register_blueprint(reviews_bp, url_prefix="/api/v1") 

# Utility Routes
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded files from /uploads folder."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/datasets/<path:filename>")
def serve_dataset_file(filename):
    """Serve dataset files (images) for frontend access."""
    datasets_folder = os.path.join(BASE_DIR, "datasets")
    return send_from_directory(datasets_folder, filename)


@app.route("/docs", methods=["GET"])
def swagger_docs():
    """Serve Swagger UI for interactive API exploration."""
    return send_from_directory(BASE_DIR, "swagger-ui.html")


@app.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    """Serve the pre-generated OpenAPI specification file."""
    return send_from_directory(BASE_DIR, "openapi.yaml")


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check for monitoring."""
    from utils.database_health import check_database_connection, get_database_pool_status
    
    db_healthy = check_database_connection()
    pool_status = get_database_pool_status()
    
    return jsonify({
        "status": "ok" if db_healthy else "error",
        "service": "SE-Textile Backend",
        "version": "2.0.0",
        "database": {
            "connection": "healthy" if db_healthy else "unhealthy",
            "uri": str(Config.SQLALCHEMY_DATABASE_URI),
            "pool": pool_status
        },
        "environment": Config.FLASK_ENV
    }), 200 if db_healthy else 503


@app.route("/admin/recover-database", methods=["POST"])
def recover_database():
    """Admin endpoint to recover database connections."""
    try:
        from utils.connection_recovery import attempt_database_recovery, get_connection_recommendations
        
        success = attempt_database_recovery()
        recommendations = get_connection_recommendations()
        
        return jsonify({
            "status": "success" if success else "error",
            "message": "Database recovery completed" if success else "Database recovery failed",
            "recommendations": recommendations
        }), 200 if success else 500
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Recovery failed: {str(e)}"
        }), 500


@app.route("/admin/db-status", methods=["GET"])
def db_status():
    """Admin endpoint to get database status."""
    try:
        from models.model import (
            db, User, Shop, Product, SalesData, StoreRegion, 
            ProductImage, Review, ExternalProduct, ExternalSalesDataItem,
            SaleOrder, SalesLineItem
        )
        
        stats = {
            "users": User.query.count(),
            "customers": User.query.filter_by(role='customer').count(),
            "shop_owners": User.query.filter_by(role='shop_owner').count(),
            "distributors": User.query.filter_by(role='distributor').count(),
            "shops": Shop.query.count(),
            "products": Product.query.count(),
            "sales_records": SalesData.query.count(),
            "store_regions": StoreRegion.query.count(),
            "product_images": ProductImage.query.count(),
            "reviews": Review.query.count(),
            "external_products": ExternalProduct.query.count(),
            "external_sales": ExternalSalesDataItem.query.count(),
            "orders": SaleOrder.query.count(),
            "order_items": SalesLineItem.query.count(),
        }
        
        # Get detailed info
        shops = Shop.query.all()
        shop_details = []
        for shop in shops:
            owner = User.query.get(shop.owner_id)
            product_count = Product.query.filter_by(shop_id=shop.id).count()
            shop_details.append({
                "name": shop.name,
                "owner": owner.username if owner else "Unknown",
                "products": product_count,
                "city": shop.city
            })
        
        return jsonify({
            "status": "success",
            "stats": stats,
            "shop_details": shop_details
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get status: {str(e)}"
        }), 500


@app.route("/", methods=["GET"])
def index():
    """Root API information."""

    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.rule.startswith("/__"):
            continue
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        routes.append({
            "path": rule.rule,
            "methods": methods,
            "endpoint": rule.endpoint
        })

    return jsonify({
        "message": "SE-Textile Unified Backend API",
        "version": "2.0.0",
        "total_routes": len(routes),
        "routes": routes
    }), 200


# Register database commands
from utils.db_commands import register_commands
register_commands(app)


# Entry Point
if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
        # Run comprehensive seeding on startup for development
        if os.getenv("AUTO_SEED", "true").lower() == "true":
            try:
                from utils.comprehensive_seeding import seed_comprehensive_data
                seed_summary = seed_comprehensive_data()
                print("Comprehensive seeding completed!")
                print("Seed summary:", seed_summary)
            except Exception as e:
                print(f"Seeding failed: {e}")
                print("Continuing with application startup...")

    print("\nRegistered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(rule)
    print("\n───────────────────────────────\n")

    app.run(host="127.0.0.1", port=5001, debug=True)
