# backend/routes/customer_routes.py
"""
Customer Portal API Routes
Provides search, discovery, and shop browsing endpoints for customers.
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, distinct, func, desc
from models.model import db, Shop, Product, ProductImage, Inventory, Review, Wishlist
from services.search_service import (
    semantic_search_products,
    search_shops,
    find_nearby_shops,
    get_search_suggestions,
    get_search_service_status,
    rebuild_search_indices
)
from utils.response_helpers import success_response, error_response, handle_exceptions
from utils.auth_utils import token_required

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
        search_result = semantic_search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
        results['products'] = search_result.get('products', [])
        results['filters'] = search_result.get('filters', {})
        results['total_products'] = len(results['products'])
    
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
    """
    Get trending products/fabrics based on user reviews.
    
    Scoring formula: (review_count * 2) + (avg_rating * 3) + recency_bonus
    - Products with more reviews rank higher
    - Products with higher average ratings rank higher
    - Products with recent reviews get a recency bonus
    """
    from datetime import datetime, timedelta
    
    limit = request.args.get('limit', 10, type=int)
    days = request.args.get('days', 30, type=int)  # Look at reviews from last N days
    
    # Calculate the date threshold for recency
    recency_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Subquery: Get review stats per product
    review_stats = db.session.query(
        Review.product_id,
        func.count(Review.id).label('review_count'),
        func.avg(Review.rating).label('avg_rating'),
        func.max(Review.created_at).label('latest_review')
    ).filter(
        Review.product_id.isnot(None)
    ).group_by(Review.product_id).subquery()
    
    # Recent reviews subquery (for recency bonus)
    recent_reviews = db.session.query(
        Review.product_id,
        func.count(Review.id).label('recent_count')
    ).filter(
        Review.product_id.isnot(None),
        Review.created_at >= recency_threshold
    ).group_by(Review.product_id).subquery()
    
    # Main query: Join products with review stats
    products_with_reviews = db.session.query(
        Product,
        func.coalesce(review_stats.c.review_count, 0).label('review_count'),
        func.coalesce(review_stats.c.avg_rating, 0).label('avg_rating'),
        func.coalesce(recent_reviews.c.recent_count, 0).label('recent_count')
    ).outerjoin(
        review_stats, Product.id == review_stats.c.product_id
    ).outerjoin(
        recent_reviews, Product.id == recent_reviews.c.product_id
    ).filter(
        Product.is_active == True
    ).order_by(
        # Trending score: (review_count * 2) + (avg_rating * 3) + (recent_count * 5)
        (func.coalesce(review_stats.c.review_count, 0) * 2 +
         func.coalesce(review_stats.c.avg_rating, 0) * 3 +
         func.coalesce(recent_reviews.c.recent_count, 0) * 5).desc(),
        Product.rating.desc()
    ).limit(limit).all()
    
    result = []
    for p, review_count, avg_rating, recent_count in products_with_reviews:
        product_dict = p.to_card_dict()
        product_dict['shop'] = p.shop.to_card_dict() if p.shop else None
        product_dict['review_count'] = int(review_count)
        product_dict['avg_rating'] = round(float(avg_rating), 1) if avg_rating else 0
        product_dict['recent_reviews'] = int(recent_count)
        
        # Add trending badge based on review activity
        if recent_count >= 3:
            product_dict['badge'] = 'Hot 🔥'
        elif review_count >= 5:
            product_dict['badge'] = 'Popular'
        elif avg_rating >= 4.5:
            product_dict['badge'] = 'Top Rated'
        else:
            product_dict['badge'] = 'Trending'
        
        # Get stock info
        if p.inventory:
            product_dict['in_stock'] = p.inventory.qty_available > 0
            product_dict['stock_qty'] = p.inventory.qty_available
        else:
            product_dict['in_stock'] = True
            product_dict['stock_qty'] = None
        
        result.append(product_dict)
    
    return jsonify({
        'status': 'success', 
        'fabrics': result, 
        'total': len(result),
        'criteria': 'review_based',
        'recency_days': days
    }), 200


@customer_bp.route('/popular-shops', methods=['GET'])
@handle_exceptions("Popular Shops")
def get_popular_shops():
    """
    Get popular shops based on user reviews and optionally nearby location.
    
    Query params:
    - limit: Number of shops to return (default: 10)
    - city: Filter by city name
    - lat: User latitude (for nearby filtering)
    - lon: User longitude (for nearby filtering)
    - radius: Search radius in km (default: 25)
    
    Scoring: (review_count * 2) + (avg_rating * 4) + (recent_reviews * 3)
    """
    from datetime import datetime, timedelta
    import math
    
    limit = request.args.get('limit', 10, type=int)
    city = request.args.get('city')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', 25, type=float)  # Default 25km
    days = request.args.get('days', 30, type=int)  # For recent reviews
    
    recency_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Subquery: Get review stats per shop
    review_stats = db.session.query(
        Review.shop_id,
        func.count(Review.id).label('review_count'),
        func.avg(Review.rating).label('avg_rating')
    ).filter(
        Review.shop_id.isnot(None)
    ).group_by(Review.shop_id).subquery()
    
    # Recent reviews subquery
    recent_reviews = db.session.query(
        Review.shop_id,
        func.count(Review.id).label('recent_count')
    ).filter(
        Review.shop_id.isnot(None),
        Review.created_at >= recency_threshold
    ).group_by(Review.shop_id).subquery()
    
    # Build main query
    query = db.session.query(
        Shop,
        func.coalesce(review_stats.c.review_count, 0).label('review_count'),
        func.coalesce(review_stats.c.avg_rating, 0).label('avg_rating'),
        func.coalesce(recent_reviews.c.recent_count, 0).label('recent_count')
    ).outerjoin(
        review_stats, Shop.id == review_stats.c.shop_id
    ).outerjoin(
        recent_reviews, Shop.id == recent_reviews.c.shop_id
    )
    
    # Apply location filter if coordinates provided
    nearby_mode = False
    if lat is not None and lon is not None:
        nearby_mode = True
        # Haversine approximation for filtering (rough bounding box first for performance)
        # 1 degree latitude ≈ 111km, 1 degree longitude ≈ 111km * cos(lat)
        lat_range = radius / 111.0
        lon_range = radius / (111.0 * math.cos(math.radians(lat)))
        
        query = query.filter(
            Shop.lat.isnot(None),
            Shop.lon.isnot(None),
            Shop.lat.between(lat - lat_range, lat + lat_range),
            Shop.lon.between(lon - lon_range, lon + lon_range)
        )
    
    # Apply city filter
    if city:
        query = query.filter(Shop.city.ilike(f'%{city}%'))
    
    # Order by popularity score
    query = query.order_by(
        # Popularity score: (review_count * 2) + (avg_rating * 4) + (recent_count * 3)
        (func.coalesce(review_stats.c.review_count, 0) * 2 +
         func.coalesce(review_stats.c.avg_rating, 0) * 4 +
         func.coalesce(recent_reviews.c.recent_count, 0) * 3).desc(),
        Shop.rating.desc()
    )
    
    shops_data = query.limit(limit * 3 if nearby_mode else limit).all()  # Get more for distance filtering
    
    result = []
    for shop, review_count, avg_rating, recent_count in shops_data:
        # Calculate actual distance if in nearby mode
        distance_km = None
        if nearby_mode and shop.lat and shop.lon:
            # Haversine formula for accurate distance
            R = 6371  # Earth radius in km
            dlat = math.radians(shop.lat - lat)
            dlon = math.radians(shop.lon - lon)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(shop.lat)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance_km = R * c
            
            # Skip if outside radius
            if distance_km > radius:
                continue
        
        shop_dict = shop.to_detail_dict()
        shop_dict['review_count'] = int(review_count)
        shop_dict['avg_rating'] = round(float(avg_rating), 1) if avg_rating else shop.rating or 0
        shop_dict['recent_reviews'] = int(recent_count)
        
        if distance_km is not None:
            shop_dict['distance'] = round(distance_km, 1)
            shop_dict['distance_text'] = f"{round(distance_km, 1)} km away"
        
        # Get product count and categories
        shop_dict['product_count'] = shop.products.filter_by(is_active=True).count()
        
        categories = db.session.query(distinct(Product.category)).filter(
            Product.shop_id == shop.id,
            Product.is_active == True,
            Product.category.isnot(None)
        ).limit(5).all()
        shop_dict['categories'] = [c[0] for c in categories if c[0]]
        
        # Add popularity badge
        if recent_count >= 3:
            shop_dict['popularity_badge'] = 'Trending 🔥'
        elif review_count >= 10:
            shop_dict['popularity_badge'] = 'Very Popular'
        elif avg_rating >= 4.5:
            shop_dict['popularity_badge'] = 'Top Rated ⭐'
        elif review_count >= 3:
            shop_dict['popularity_badge'] = 'Popular'
        
        result.append(shop_dict)
        
        if len(result) >= limit:
            break
    
    # Sort by distance if in nearby mode
    if nearby_mode:
        result.sort(key=lambda x: (-(x.get('avg_rating', 0)), x.get('distance', 999)))
    
    return jsonify({
        'status': 'success', 
        'shops': result, 
        'total': len(result),
        'criteria': 'review_based',
        'nearby_mode': nearby_mode,
        'radius_km': radius if nearby_mode else None
    }), 200


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
            'comment': r.body,
            'user_name': r.reviewer.full_name if r.reviewer else (r.user_name or 'Anonymous'),
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
        # Force stock for demo
        stock_qty = p.inventory.qty_available if p.inventory else 0
        if stock_qty == 0:
            stock_qty = 100
            
        product_dict['in_stock'] = stock_qty > 0
        product_dict['stock_qty'] = stock_qty
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
    sort_by = request.args.get('sort', 'rating')  # rating, price_asc, price_desc, newest, distance
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
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
    elif sort_by == 'distance' and lat is not None and lon is not None:
        # Join with Shop to access location
        query = query.join(Shop)
        # Calculate squared Euclidean distance for sorting (faster than Haversine and sufficient for sorting)
        # (lat1-lat2)^2 + (lon1-lon2)^2
        distance_expr = func.pow(Shop.lat - lat, 2) + func.pow(Shop.lon - lon, 2)
        query = query.order_by(distance_expr.asc())
    else:
        query = query.order_by(Product.rating.desc(), Product.is_trending.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    products = []
    for p in pagination.items:
        product_dict = p.to_card_dict()
        product_dict['shop'] = p.shop.to_card_dict() if p.shop else None
        
        # Force stock for demo
        stock_qty = p.inventory.qty_available if p.inventory else 0
        if stock_qty == 0:
            stock_qty = 100
            
        product_dict['in_stock'] = stock_qty > 0
        product_dict['stock_qty'] = stock_qty
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
    
    # Force stock for demo
    stock_qty = product.inventory.qty_available if product.inventory else 0
    if stock_qty == 0:
        stock_qty = 100
        
    product_dict['in_stock'] = stock_qty > 0
    product_dict['stock_qty'] = stock_qty
    
    # Get reviews for product
    reviews = product.reviews.order_by(Review.created_at.desc()).limit(10).all()
    product_dict['reviews'] = [
        {
            'id': r.id,
            'rating': r.rating,
            'comment': r.body,
            'user_name': r.reviewer.full_name if r.reviewer else (r.user_name or 'Anonymous'),
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


# ============================================================================
# WISHLIST ENDPOINTS
# ============================================================================

@customer_bp.route('/wishlist', methods=['GET'])
@token_required
@handle_exceptions("Get Wishlist")
def get_wishlist(current_user):
    """Get current user's wishlist."""
    current_user_id = current_user.get('id')
    
    wishlist_items = Wishlist.query.filter_by(user_id=current_user_id).all()
    
    products = []
    for item in wishlist_items:
        if item.product and item.product.is_active:
            product_dict = item.product.to_card_dict()
            product_dict['added_at'] = item.created_at.isoformat()
            products.append(product_dict)
            
    return success_response(data={'wishlist': products, 'count': len(products)})


@customer_bp.route('/wishlist/<int:product_id>', methods=['POST'])
@token_required
@handle_exceptions("Add to Wishlist")
def add_to_wishlist(current_user, product_id):
    """Add product to wishlist."""
    current_user_id = current_user.get('id')
    
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)
        
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user_id, product_id=product_id).first()
    if existing:
        return success_response(message="Product already in wishlist")
        
    wishlist_item = Wishlist(user_id=current_user_id, product_id=product_id)
    db.session.add(wishlist_item)
    db.session.commit()
    
    return success_response(message="Added to wishlist")


@customer_bp.route('/wishlist/<int:product_id>', methods=['DELETE'])
@token_required
@handle_exceptions("Remove from Wishlist")
def remove_from_wishlist(current_user, product_id):
    """Remove product from wishlist."""
    current_user_id = current_user.get('id')
    
    wishlist_item = Wishlist.query.filter_by(user_id=current_user_id, product_id=product_id).first()
    if not wishlist_item:
        return error_response("Item not in wishlist", 404)
        
    db.session.delete(wishlist_item)
    db.session.commit()
    
    return success_response(message="Removed from wishlist")

