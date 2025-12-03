# backend/routes/customer_routes.py
"""
Customer Portal API Routes
Provides search, discovery, and shop browsing endpoints for customers.
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, distinct, func, desc
from models.model import db, Shop, Product, ProductImage, Inventory, Review
from services.search_service import (
    semantic_search_products,
    search_shops,
    find_nearby_shops,
    get_search_suggestions,
    get_search_service_status,
    rebuild_search_indices
)
from utils.response_helpers import success_response, error_response, handle_exceptions

customer_bp = Blueprint('customer', __name__)


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@customer_bp.route('/search', methods=['GET'])
@handle_exceptions("Customer Search")
def unified_search():
    """
    Unified semantic search for products and shops.
    
    Query params:
    - q: Search query (required)
    - type: 'all', 'products', 'shops' (default: 'all')
    - category: Filter by category
    - city: Filter by city (for shops)
    - min_price: Minimum price (for products)
    - max_price: Maximum price (for products)
    - min_rating: Minimum rating
    - limit: Results per type (default: 20)
    """
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    category = request.args.get('category')
    city = request.args.get('city')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return error_response("Search query is required", 400)
    
    results = {
        'query': query,
        'products': [],
        'shops': [],
        'total_products': 0,
        'total_shops': 0
    }
    
    # Search products
    if search_type in ['all', 'products']:
        products = semantic_search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
        results['products'] = products
        results['total_products'] = len(products)
    
    # Search shops
    if search_type in ['all', 'shops']:
        shops = search_shops(
            query=query,
            city=city,
            has_product_category=category,
            min_rating=min_rating,
            limit=limit
        )
        results['shops'] = shops
        results['total_shops'] = len(shops)
    
    return success_response(data=results)


@customer_bp.route('/search/suggestions', methods=['GET'])
@handle_exceptions("Search Suggestions")
def search_suggestions():
    """
    Get autocomplete suggestions for search.
    
    Query params:
    - q: Partial search query (min 2 chars)
    - limit: Max suggestions per type (default: 5)
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 5, type=int)
    
    if len(query) < 2:
        return success_response(data={'products': [], 'shops': [], 'categories': []})
    
    suggestions = get_search_suggestions(query, limit)
    return success_response(data=suggestions)


@customer_bp.route('/search/nearby', methods=['GET', 'POST'])
@handle_exceptions("Nearby Search")
def nearby_search():
    """
    Find nearby shops with optional product search.
    
    Query params / Body:
    - lat: Latitude (required)
    - lon: Longitude (required)
    - radius: Search radius in km (default: 10)
    - product_query: Optional product search within nearby shops
    - category: Filter by product category
    - limit: Max results (default: 20)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args.to_dict()
    
    lat = data.get('lat') or data.get('latitude')
    lon = data.get('lon') or data.get('longitude')
    
    if lat is None or lon is None:
        return error_response("Latitude and longitude are required", 400)
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return error_response("Invalid coordinates", 400)
    
    radius = float(data.get('radius', 10))
    product_query = data.get('product_query') or data.get('q')
    category = data.get('category')
    limit = int(data.get('limit', 20))
    
    # Validate radius (100m to 50km)
    radius = max(0.1, min(50, radius))
    
    shops = find_nearby_shops(
        lat=lat,
        lon=lon,
        radius_km=radius,
        product_query=product_query,
        category=category,
        limit=limit
    )
    
    return success_response(data={
        'shops': shops,
        'total': len(shops),
        'search_location': {'lat': lat, 'lon': lon},
        'radius_km': radius
    })


# ============================================================================
# TRENDING & POPULAR ENDPOINTS
# ============================================================================

@customer_bp.route('/trending-fabrics', methods=['GET'])
@handle_exceptions("Trending Fabrics")
def get_trending_fabrics():
    """Get trending products/fabrics based on sales and ratings."""
    limit = request.args.get('limit', 10, type=int)
    
    # Get trending products
    products = Product.query.filter(
        Product.is_active == True
    ).order_by(
        Product.is_trending.desc(),
        Product.rating.desc()
    ).limit(limit).all()
    
    result = []
    for p in products:
        product_dict = p.to_card_dict()
        product_dict['shop'] = p.shop.to_card_dict() if p.shop else None
        
        # Get stock info
        if p.inventory:
            product_dict['in_stock'] = p.inventory.qty_available > 0
            product_dict['stock_qty'] = p.inventory.qty_available
        else:
            product_dict['in_stock'] = True
            product_dict['stock_qty'] = None
        
        result.append(product_dict)
    
    return jsonify({'status': 'success', 'fabrics': result, 'total': len(result)}), 200


@customer_bp.route('/popular-shops', methods=['GET'])
@handle_exceptions("Popular Shops")
def get_popular_shops():
    """Get popular shops based on ratings and activity."""
    limit = request.args.get('limit', 10, type=int)
    city = request.args.get('city')
    
    query = Shop.query
    
    if city:
        query = query.filter(Shop.city.ilike(f'%{city}%'))
    
    shops = query.order_by(
        Shop.is_popular.desc(),
        Shop.rating.desc()
    ).limit(limit).all()
    
    result = []
    for shop in shops:
        shop_dict = shop.to_detail_dict()
        
        # Get product count and categories
        shop_dict['product_count'] = shop.products.filter_by(is_active=True).count()
        
        categories = db.session.query(distinct(Product.category)).filter(
            Product.shop_id == shop.id,
            Product.is_active == True,
            Product.category.isnot(None)
        ).limit(5).all()
        shop_dict['categories'] = [c[0] for c in categories if c[0]]
        
        result.append(shop_dict)
    
    return jsonify({'status': 'success', 'shops': result, 'total': len(result)}), 200


# ============================================================================
# SHOP BROWSING ENDPOINTS
# ============================================================================

@customer_bp.route('/shops/shops', methods=['GET'])
@handle_exceptions("All Shops")
def get_all_shops():
    """Get all shops with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    city = request.args.get('city')
    category = request.args.get('category')
    sort_by = request.args.get('sort', 'rating')  # rating, name, newest
    
    query = Shop.query
    
    if city:
        query = query.filter(Shop.city.ilike(f'%{city}%'))
    
    if category:
        query = query.join(Product).filter(
            Product.category.ilike(f'%{category}%'),
            Product.is_active == True
        ).distinct()
    
    # Sorting
    if sort_by == 'name':
        query = query.order_by(Shop.name.asc())
    elif sort_by == 'newest':
        query = query.order_by(Shop.created_at.desc())
    else:
        query = query.order_by(Shop.rating.desc(), Shop.is_popular.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    shops = []
    for shop in pagination.items:
        shop_dict = shop.to_detail_dict()
        shop_dict['product_count'] = shop.products.filter_by(is_active=True).count()
        shops.append(shop_dict)
    
    return success_response(data={
        'shops': shops,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@customer_bp.route('/shops/shop/<int:shop_id>', methods=['GET'])
@handle_exceptions("Shop Details")
def get_shop_details(shop_id):
    """Get detailed shop information including products."""
    shop = Shop.query.get(shop_id)
    if not shop:
        return error_response("Shop not found", 404)
    
    shop_dict = shop.to_detail_dict(include_owner=False)
    
    # Get shop products
    products = shop.products.filter_by(is_active=True).order_by(
        Product.rating.desc()
    ).limit(20).all()
    
    shop_dict['products'] = [p.to_card_dict() for p in products]
    shop_dict['product_count'] = shop.products.filter_by(is_active=True).count()
    
    # Get categories
    categories = db.session.query(distinct(Product.category)).filter(
        Product.shop_id == shop.id,
        Product.is_active == True,
        Product.category.isnot(None)
    ).all()
    shop_dict['categories'] = [c[0] for c in categories if c[0]]
    
    # Get recent reviews
    reviews = shop.reviews.order_by(Review.created_at.desc()).limit(5).all()
    shop_dict['recent_reviews'] = [
        {
            'id': r.id,
            'rating': r.rating,
            'comment': r.comment,
            'user_name': r.user.full_name if r.user else 'Anonymous',
            'created_at': r.created_at.isoformat() if r.created_at else None
        }
        for r in reviews
    ]
    
    return success_response(data={'shop': shop_dict})


@customer_bp.route('/shops/shop/<int:shop_id>/products', methods=['GET'])
@handle_exceptions("Shop Products")
def get_shop_products(shop_id):
    """Get products from a specific shop with filtering."""
    shop = Shop.query.get(shop_id)
    if not shop:
        return error_response("Shop not found", 404)
    
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock', type=bool)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Product.query.filter(
        Product.shop_id == shop_id,
        Product.is_active == True
    )
    
    if category:
        query = query.filter(Product.category.ilike(f'%{category}%'))
    
    if search:
        pattern = f'%{search}%'
        query = query.filter(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern)
            )
        )
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if in_stock:
        query = query.join(Inventory).filter(Inventory.qty_available > 0)
    
    pagination = query.order_by(Product.rating.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    products = []
    for p in pagination.items:
        product_dict = p.to_card_dict()
        if p.inventory:
            product_dict['in_stock'] = p.inventory.qty_available > 0
            product_dict['stock_qty'] = p.inventory.qty_available
        products.append(product_dict)
    
    return success_response(data={
        'products': products,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


# ============================================================================
# PRODUCT BROWSING ENDPOINTS
# ============================================================================

@customer_bp.route('/products', methods=['GET'])
@handle_exceptions("Browse Products")
def browse_products():
    """Browse products with filtering and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'rating')  # rating, price_asc, price_desc, newest
    
    query = Product.query.filter(Product.is_active == True)
    
    if category:
        query = query.filter(Product.category.ilike(f'%{category}%'))
    
    if search:
        pattern = f'%{search}%'
        query = query.filter(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Product.category.ilike(pattern)
            )
        )
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.rating.desc(), Product.is_trending.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    products = []
    for p in pagination.items:
        product_dict = p.to_card_dict()
        product_dict['shop'] = p.shop.to_card_dict() if p.shop else None
        if p.inventory:
            product_dict['in_stock'] = p.inventory.qty_available > 0
        products.append(product_dict)
    
    return jsonify({
        'status': 'success',
        'products': products,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@customer_bp.route('/products/<int:product_id>', methods=['GET'])
@handle_exceptions("Product Details")
def get_product_details(product_id):
    """Get detailed product information."""
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return error_response("Product not found", 404)
    
    product_dict = product.to_detail_dict(include_shop=True, include_inventory=True)
    
    # Get reviews for product
    reviews = product.reviews.order_by(Review.created_at.desc()).limit(10).all()
    product_dict['reviews'] = [
        {
            'id': r.id,
            'rating': r.rating,
            'comment': r.comment,
            'user_name': r.user.full_name if r.user else 'Anonymous',
            'created_at': r.created_at.isoformat() if r.created_at else None
        }
        for r in reviews
    ]
    
    # Get similar products
    if product.category:
        similar = Product.query.filter(
            Product.id != product.id,
            Product.category == product.category,
            Product.is_active == True
        ).order_by(Product.rating.desc()).limit(6).all()
        product_dict['similar_products'] = [p.to_card_dict() for p in similar]
    
    return jsonify({'status': 'success', 'product': product_dict}), 200


@customer_bp.route('/categories', methods=['GET'])
@handle_exceptions("Categories")
def get_categories():
    """Get all product categories with counts."""
    categories = db.session.query(
        Product.category,
        func.count(Product.id).label('count')
    ).filter(
        Product.is_active == True,
        Product.category.isnot(None)
    ).group_by(Product.category).order_by(desc('count')).all()
    
    result = [
        {'name': cat, 'count': count}
        for cat, count in categories if cat
    ]
    
    return jsonify({'status': 'success', 'categories': result}), 200


# ============================================================================
# SERVICE STATUS
# ============================================================================

@customer_bp.route('/search/status', methods=['GET'])
@handle_exceptions("Search Status")
def search_status():
    """Get search service status."""
    status = get_search_service_status()
    return success_response(data=status)


@customer_bp.route('/search/rebuild', methods=['POST'])
@handle_exceptions("Rebuild Index")
def rebuild_index():
    """Rebuild search indices (admin only in production)."""
    result = rebuild_search_indices()
    return success_response(data=result)
