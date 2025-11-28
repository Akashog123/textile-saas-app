"""
Database Management and Seeding Script

This script provides commands for database management:
- seed: Run comprehensive role-based seeding
- seed-minimal: Run minimal seeding (existing logic)
- reset: Clear all data
- status: Show database status
"""

import click
from flask.cli import with_appcontext

from utils.seed_data import seed_minimal_data
from utils.comprehensive_seeding import seed_comprehensive_data
from models.model import db, User, Shop, Product, SalesData

@click.command()
@with_appcontext
def seed():
    """Run comprehensive role-based data seeding (mainly for development/reset)."""
    print("Starting comprehensive role-based seeding...")
    try:
        result = seed_comprehensive_data()
        print("Comprehensive seeding completed successfully!")
        print(f"Summary: {result}")
        print("Note: Seeding normally runs automatically on app startup")
    except Exception as e:
        print(f"Seeding failed: {e}")
        raise

@click.command()
@with_appcontext
def seed_minimal():
    """Run minimal data seeding (legacy - for testing only)."""
    print("Starting minimal seeding...")
    try:
        result = seed_minimal_data()
        print("Minimal seeding completed!")
        print(f"Summary: {result}")
        print("Note: Comprehensive seeding runs automatically on app startup")
    except Exception as e:
        print(f"Minimal seeding failed: {e}")
        raise

@click.command()
@with_appcontext
def reset_db():
    """Reset database - clear all data."""
    print("This will delete ALL data. Are you sure?")
    if click.confirm('Do you want to continue?'):
        print("Clearing all data...")
        try:
            # Delete in order of dependencies
            SalesData.query.delete()
            Product.query.delete()
            Shop.query.delete()
            User.query.delete()
            
            db.session.commit()
            print("Database reset completed!")
        except Exception as e:
            db.session.rollback()
            print(f"Database reset failed: {e}")
            raise

@click.command()
@with_appcontext
def db_status():
    """Show database status and statistics."""
    print("📊 Database Status:")
    print("=" * 40)
    
    try:
        from models.model import (
            User, Shop, Product, SalesData, StoreRegion, 
            ProductImage, Review, ExternalProduct, ExternalSalesDataItem,
            SaleOrder, SalesLineItem
        )
        
        stats = {
            "Users": User.query.count(),
            "Customers": User.query.filter_by(role='customer').count(),
            "Shop Owners": User.query.filter_by(role='shop_owner').count(),
            "Distributors": User.query.filter_by(role='distributor').count(),
            "Shops": Shop.query.count(),
            "Products": Product.query.count(),
            "Sales Records": SalesData.query.count(),
            "Store Regions": StoreRegion.query.count(),
            "Product Images": ProductImage.query.count(),
            "Reviews": Review.query.count(),
            "External Products": ExternalProduct.query.count(),
            "External Sales": ExternalSalesDataItem.query.count(),
            "Orders": SaleOrder.query.count(),
            "Order Items": SalesLineItem.query.count(),
        }
        
        for entity, count in stats.items():
            print(f"{entity}: {count}")
        
        # Show shop details
        shops = Shop.query.all()
        if shops:
            print(f"\n🏪 Shop Details:")
            for shop in shops:
                owner = User.query.get(shop.owner_id)
                product_count = Product.query.filter_by(shop_id=shop.id).count()
                print(f"  - {shop.name} (Owner: {owner.username if owner else 'Unknown'}, Products: {product_count})")
        
        # Show user accounts
        print(f"\n👥 User Accounts:")
        users = User.query.all()
        for user in users:
            shops_count = Shop.query.filter_by(owner_id=user.id).count()
            products_count = Product.query.join(Shop, Product.shop_id == Shop.id).filter(Shop.owner_id == user.id).count()
            print(f"  - {user.username} ({user.role}): {shops_count} shops, {products_count} products")
            
    except Exception as e:
        print(f"Failed to get status: {e}")

@click.command()
@with_appcontext
def seed_demo():
    """Create demo accounts with sample data for testing."""
    print("🎭 Creating demo accounts...")
    
    from werkzeug.security import generate_password_hash
    
    # Create demo users if they don't exist
    demo_users = [
        {
            "username": "demo_customer",
            "email": "customer@demo.com",
            "password": "Demo123",
            "role": "customer",
            "full_name": "Demo Customer"
        },
        {
            "username": "demo_shopowner",
            "email": "shopowner@demo.com", 
            "password": "Demo123",
            "role": "shop_owner",
            "full_name": "Demo Shop Owner"
        },
        {
            "username": "demo_distributor",
            "email": "distributor@demo.com",
            "password": "Demo123", 
            "role": "distributor",
            "full_name": "Demo Distributor"
        }
    ]
    
    created = 0
    for user_data in demo_users:
        existing = User.query.filter_by(username=user_data["username"]).first()
        if not existing:
            user = User(
                full_name=user_data["full_name"],
                username=user_data["username"],
                email=user_data["email"],
                password=generate_password_hash(user_data["password"]),
                role=user_data["role"],
                approved=True,
                city="Demo City",
                state="Demo State"
            )
            db.session.add(user)
            created += 1
    
    if created > 0:
        db.session.commit()
        print(f"Created {created} demo accounts!")
        print("\nDemo Login Credentials:")
        for user_data in demo_users:
            print(f"  {user_data['role']}: {user_data['username']} / {user_data['password']}")
    else:
        print("Demo accounts already exist!")

# Register commands
def register_commands(app):
    """Register CLI commands with Flask app."""
    app.cli.add_command(seed)
    app.cli.add_command(seed_minimal)
    app.cli.add_command(reset_db)
    app.cli.add_command(db_status)
    app.cli.add_command(seed_demo)
