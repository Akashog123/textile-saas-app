# backend/routes/supply_chain_routes.py
"""
Supply Chain Routes
Manages shop-distributor supply relationships.
These routes complement the main distributor_routes.py which handles analytics.
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from models.model import db, User, Shop, Product, Inventory, DistributorSupply
from utils.auth_utils import token_required, roles_required
from utils.response_helpers import success_response, error_response, handle_exceptions


supply_chain_bp = Blueprint('supply_chain', __name__)


# ============================================================================
# SHOP OWNER ENDPOINTS
# ============================================================================

@supply_chain_bp.route('/shop/suppliers', methods=['GET'])
@token_required
@roles_required('shop_owner')
@handle_exceptions("Get Shop Suppliers")
def get_shop_suppliers(current_user):
    """
    Get all distributors who supply products to shop owner's shops.
    Groups by distributor showing total products and supply value.
    """
    # Get shops owned by current user
    shops = Shop.query.filter_by(owner_id=current_user.id).all()
    shop_ids = [s.id for s in shops]
    
    if not shop_ids:
        return success_response(data={'suppliers': [], 'summary': {}})
    
    # Get supply records grouped by distributor
    supplies = db.session.query(
        DistributorSupply.distributor_id,
        func.count(DistributorSupply.id).label('product_count'),
        func.sum(DistributorSupply.quantity_supplied).label('total_quantity'),
    ).filter(
        DistributorSupply.shop_id.in_(shop_ids),
        DistributorSupply.status == 'completed'
    ).group_by(DistributorSupply.distributor_id).all()
    
    suppliers_data = []
    for supply in supplies:
        distributor = User.query.get(supply.distributor_id)
        if distributor:
            suppliers_data.append({
                'distributor_id': distributor.id,
                'distributor_name': distributor.full_name or distributor.username,
                'distributor_contact': distributor.contact,
                'distributor_city': distributor.city,
                'products_supplied': supply.product_count,
                'total_quantity': supply.total_quantity or 0
            })
    
    return success_response(data={
        'suppliers': suppliers_data,
        'summary': {
            'total_suppliers': len(suppliers_data),
            'total_products_supplied': sum(s['products_supplied'] for s in suppliers_data)
        }
    })


@supply_chain_bp.route('/shop/<int:shop_id>/supply-details', methods=['GET'])
@token_required
@roles_required('shop_owner')
@handle_exceptions("Get Shop Supply Details")
def get_shop_supply_details(current_user, shop_id):
    """Get detailed supply records for a specific shop."""
    # Verify ownership
    shop = Shop.query.filter_by(id=shop_id, owner_id=current_user.id).first()
    if not shop:
        return error_response("Shop not found or not owned by you", 404)
    
    # Get all supply records for this shop
    supplies = DistributorSupply.query.filter_by(
        shop_id=shop_id,
        status='completed'
    ).order_by(DistributorSupply.supply_date.desc()).all()
    
    supply_records = []
    for s in supplies:
        distributor = User.query.get(s.distributor_id)
        product = Product.query.get(s.product_id)
        
        supply_records.append({
            'id': s.id,
            'distributor_name': distributor.full_name if distributor else 'Unknown',
            'product_name': product.name if product else 'Unknown',
            'product_id': s.product_id,
            'quantity': s.quantity_supplied,
            'unit_price': float(s.unit_price) if s.unit_price else 0,
            'total_value': float(s.total_value) if s.total_value else 0,
            'supply_date': s.supply_date.isoformat() if s.supply_date else None
        })
    
    return success_response(data={'supply_records': supply_records})


# ============================================================================
# DISTRIBUTOR ENDPOINTS
# ============================================================================

@supply_chain_bp.route('/distributor/supplied-shops', methods=['GET'])
@token_required
@roles_required('distributor', 'manufacturer')
@handle_exceptions("Get Supplied Shops")
def get_supplied_shops(current_user):
    """
    Get all shops this distributor supplies products to.
    Groups by shop showing product count and supply summary.
    """
    # Get supply records grouped by shop
    supplies = db.session.query(
        DistributorSupply.shop_id,
        func.count(DistributorSupply.product_id.distinct()).label('product_count'),
        func.sum(DistributorSupply.quantity_supplied).label('total_quantity'),
    ).filter(
        DistributorSupply.distributor_id == current_user.id,
        DistributorSupply.status == 'completed'
    ).group_by(DistributorSupply.shop_id).all()
    
    shops_data = []
    for supply in supplies:
        shop = Shop.query.get(supply.shop_id)
        if shop:
            shops_data.append({
                'shop_id': shop.id,
                'shop_name': shop.name,
                'shop_city': shop.city,
                'shop_address': shop.address,
                'products_supplied': supply.product_count,
                'total_quantity': supply.total_quantity or 0,
                'lat': shop.lat,
                'lon': shop.lon
            })
    
    return success_response(data={
        'shops': shops_data,
        'summary': {
            'total_shops': len(shops_data),
            'total_products': sum(s['products_supplied'] for s in shops_data),
            'total_quantity': sum(s['total_quantity'] for s in shops_data)
        }
    })


@supply_chain_bp.route('/distributor/shop/<int:shop_id>/products', methods=['GET'])
@token_required
@roles_required('distributor', 'manufacturer')
@handle_exceptions("Get Supplied Products")
def get_supplied_products(current_user, shop_id):
    """Get all products this distributor supplies to a specific shop."""
    # Get supply records for this shop
    supplies = DistributorSupply.query.filter_by(
        distributor_id=current_user.id,
        shop_id=shop_id,
        status='completed'
    ).all()
    
    if not supplies:
        return success_response(data={'products': [], 'shop': None})
    
    shop = Shop.query.get(shop_id)
    
    products_data = []
    for s in supplies:
        product = Product.query.get(s.product_id)
        if product:
            inventory = product.inventory
            products_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'retail_price': float(product.price) if product.price else 0,
                'supply_price': float(s.unit_price) if s.unit_price else 0,
                'quantity_supplied': s.quantity_supplied,
                'current_stock': inventory.qty_available if inventory else 0,
                'safety_stock': inventory.safety_stock if inventory else 0,
                'needs_restock': (inventory.qty_available <= inventory.safety_stock) if inventory else True
            })
    
    return success_response(data={
        'products': products_data,
        'shop': {
            'id': shop.id,
            'name': shop.name,
            'city': shop.city
        } if shop else None
    })


@supply_chain_bp.route('/distributor/low-stock-alerts', methods=['GET'])
@token_required
@roles_required('distributor', 'manufacturer')
@handle_exceptions("Get Low Stock Alerts")
def get_low_stock_alerts(current_user):
    """Get products that need restocking across all supplied shops."""
    # Get all products this distributor supplies
    supplies = DistributorSupply.query.filter_by(
        distributor_id=current_user.id,
        status='completed'
    ).all()
    
    alerts = []
    for s in supplies:
        product = Product.query.get(s.product_id)
        if not product:
            continue
        
        inventory = product.inventory
        if not inventory:
            continue
        
        # Check if stock is at or below safety level
        if inventory.qty_available <= inventory.safety_stock:
            shop = Shop.query.get(s.shop_id)
            alerts.append({
                'product_id': product.id,
                'product_name': product.name,
                'shop_id': s.shop_id,
                'shop_name': shop.name if shop else 'Unknown',
                'current_stock': inventory.qty_available,
                'safety_stock': inventory.safety_stock,
                'last_supplied': s.quantity_supplied,
                'urgency': 'critical' if inventory.qty_available == 0 else 'low'
            })
    
    # Sort by urgency (critical first) then by current stock
    alerts.sort(key=lambda x: (0 if x['urgency'] == 'critical' else 1, x['current_stock']))
    
    return success_response(data={
        'alerts': alerts,
        'summary': {
            'critical_count': len([a for a in alerts if a['urgency'] == 'critical']),
            'low_count': len([a for a in alerts if a['urgency'] == 'low']),
            'total_alerts': len(alerts)
        }
    })
