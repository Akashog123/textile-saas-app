"""
Account and Shop Creation Seeding for SE Textile App

This script creates user accounts and shops for different roles:
- Creates Customer accounts
- Creates Shop Manager accounts with assigned shops
- Creates Distributor accounts
"""

from typing import Dict, Any, List

from werkzeug.security import generate_password_hash

from models.model import db, User, Shop, Product, DistributorSupply

# Seeding limits
MAX_CUSTOMERS = 3
MAX_SHOP_MANAGERS = 3
MAX_DISTRIBUTORS = 2

# User credentials
USER_CREDENTIALS = {
    "customers": [
        {"username": "customer1", "email": "customer1@example.com", "password": "Customer123"},
        {"username": "customer2", "email": "customer2@example.com", "password": "Customer123"},
        {"username": "customer3", "email": "customer3@example.com", "password": "Customer123"},
    ],
    "shop_managers": [
        {"username": "shopowner1", "email": "shopowner1@example.com", "password": "ShopOwner123"},
        {"username": "shopowner2", "email": "shopowner2@example.com", "password": "ShopOwner123"},
        {"username": "shopowner3", "email": "shopowner3@example.com", "password": "ShopOwner123"},
    ],
    "distributors": [
        {"username": "distributor1", "email": "distributor1@example.com", "password": "Distributor123"},
        {"username": "distributor2", "email": "distributor2@example.com", "password": "Distributor123"},
    ]
}

# Shop data for shop managers
SHOP_DATA = [
    {
        "name": "Royal Silk Emporium",
        "description": "Premium silk sarees and traditional wear",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Zaveri Bazaar, Mumbai",
        "lat": 19.0760,
        "lon": 72.8777
    },
    {
        "name": "Fashion Hub Textiles",
        "description": "Modern and contemporary textile collections",
        "city": "Delhi",
        "state": "Delhi",
        "address": "Chandni Chowk, Delhi",
        "lat": 28.7041,
        "lon": 77.1025
    },
    {
        "name": "Heritage Weaves",
        "description": "Handloom and artisanal textile treasures",
        "city": "Jaipur",
        "state": "Rajasthan",
        "address": "Johari Bazaar, Jaipur",
        "lat": 26.9124,
        "lon": 75.7873
    }
]


def create_users() -> Dict[str, List[User]]:
    """Create users for different roles."""
    created_users = {"customers": [], "shop_managers": [], "distributors": []}
    
    # Create customers
    for i, cred in enumerate(USER_CREDENTIALS["customers"][:MAX_CUSTOMERS]):
        user = User.query.filter_by(username=cred["username"]).first()
        if not user:
            user = User(
                full_name=f"Customer {i+1}",
                username=cred["username"],
                email=cred["email"],
                password=generate_password_hash(cred["password"]),
                role="customer",
                approved=True,
                city=f"City {i+1}",
                state=f"State {i+1}",
                contact=f"+91{9000000000 + i}"
            )
            db.session.add(user)
            db.session.flush()
        created_users["customers"].append(user)
    
    # Create shop managers with their city/state from SHOP_DATA
    for i, cred in enumerate(USER_CREDENTIALS["shop_managers"][:MAX_SHOP_MANAGERS]):
        user = User.query.filter_by(username=cred["username"]).first()
        if not user:
            shop_info = SHOP_DATA[i] if i < len(SHOP_DATA) else {"city": f"City {i+1}", "state": f"State {i+1}"}
            user = User(
                full_name=f"Shop Owner {i+1}",
                username=cred["username"],
                email=cred["email"],
                password=generate_password_hash(cred["password"]),
                role="shop_owner",
                approved=True,
                city=shop_info["city"],
                state=shop_info["state"],
                contact=f"+91{8000000000 + i}"
            )
            db.session.add(user)
            db.session.flush()
        created_users["shop_managers"].append(user)
    
    # Create distributors
    for i, cred in enumerate(USER_CREDENTIALS["distributors"][:MAX_DISTRIBUTORS]):
        user = User.query.filter_by(username=cred["username"]).first()
        if not user:
            user = User(
                full_name=f"Distributor {i+1}",
                username=cred["username"],
                email=cred["email"],
                password=generate_password_hash(cred["password"]),
                role="distributor",
                approved=True,
                city=f"Distributor City {i+1}",
                state=f"Distributor State {i+1}",
                contact=f"+91{7000000000 + i}"
            )
            db.session.add(user)
            db.session.flush()
        created_users["distributors"].append(user)
    
    return created_users


def create_shops(shop_managers: List[User]) -> List[Shop]:
    """Create shops for shop managers."""
    created_shops = []
    
    for i, manager in enumerate(shop_managers):
        if i >= len(SHOP_DATA):
            break
        
        shop_data = SHOP_DATA[i]
        
        # Check if shop already exists for this manager
        existing_shop = Shop.query.filter_by(owner_id=manager.id).first()
        if existing_shop:
            created_shops.append(existing_shop)
            continue
        
        # Check if shop with same name exists
        existing_by_name = Shop.query.filter_by(name=shop_data["name"]).first()
        if existing_by_name:
            created_shops.append(existing_by_name)
            continue
        
        shop = Shop(
            name=shop_data["name"],
            description=shop_data["description"],
            address=shop_data["address"],
            city=shop_data["city"],
            state=shop_data["state"],
            location=f"{shop_data['city']}, {shop_data['state']}",
            lat=shop_data["lat"],
            lon=shop_data["lon"],
            rating=0.0,
            is_popular=True,
            owner_id=manager.id
        )
        db.session.add(shop)
        db.session.flush()
        created_shops.append(shop)
    
    return created_shops


def create_distributor_partnerships(distributors: List[User], shops: List[Shop]) -> int:
    """
    Create DistributorSupply records linking distributors to shop products.
    Each distributor supplies products to shops.
    """
    partnerships_created = 0
    
    if not distributors or not shops:
        print("[Seed] No distributors or shops available for partnerships")
        return 0
    
    # For each shop, get its products and assign them to distributors
    for shop in shops:
        # Get products for this shop
        products = Product.query.filter_by(shop_id=shop.id, is_active=True).all()
        
        if not products:
            print(f"[Seed] No products found for shop {shop.name}, skipping")
            continue
        
        # Distribute products among distributors (round-robin)
        for i, product in enumerate(products):
            distributor = distributors[i % len(distributors)]
            
            # Check if supply record already exists
            existing = DistributorSupply.query.filter_by(
                distributor_id=distributor.id,
                product_id=product.id,
                shop_id=shop.id
            ).first()
            
            if not existing:
                supply = DistributorSupply(
                    distributor_id=distributor.id,
                    product_id=product.id,
                    shop_id=shop.id,
                    quantity_supplied=100,  # Initial supply quantity
                    unit_price=float(product.price) * 0.7 if product.price else 0,  # 70% of retail price
                    status='completed'
                )
                db.session.add(supply)
                partnerships_created += 1
        
        print(f"[Seed] Created {len(products)} supply records for shop: {shop.name}")
    
    return partnerships_created


def seed_comprehensive_data() -> Dict[str, Any]:
    """Main seeding function for user accounts, shops, and distributor partnerships."""
    print("[Seed] Starting comprehensive seeding...")
    
    summary = {
        "users_created": 0,
        "customers_created": 0,
        "shop_managers_created": 0,
        "distributors_created": 0,
        "shops_created": 0,
        "partnerships_created": 0,
        "errors": []
    }
    
    try:
        # Create users
        print("[Seed] Creating user accounts...")
        users = create_users()
        
        summary["customers_created"] = len(users["customers"])
        summary["shop_managers_created"] = len(users["shop_managers"])
        summary["distributors_created"] = len(users["distributors"])
        summary["users_created"] = (
            summary["customers_created"] + 
            summary["shop_managers_created"] + 
            summary["distributors_created"]
        )
        
        # Create shops for shop managers
        print("[Seed] Creating shops for shop managers...")
        shops = create_shops(users["shop_managers"])
        summary["shops_created"] = len(shops)
        
        # Create distributor partnerships
        print("[Seed] Creating distributor-shop partnerships...")
        partnerships = create_distributor_partnerships(users["distributors"], shops)
        summary["partnerships_created"] = partnerships
        
        # Commit all changes
        db.session.commit()
        
        print("[Seed] Comprehensive seeding completed successfully!")
        print(f"[Seed] Created: {summary['customers_created']} customers, {summary['shop_managers_created']} shop managers, {summary['distributors_created']} distributors")
        print(f"[Seed] Created: {summary['shops_created']} shops, {summary['partnerships_created']} partnerships")
        
        # Print login credentials
        print("\n[Seed] Login Credentials:")
        print("=" * 50)
        for role, credentials in USER_CREDENTIALS.items():
            print(f"\n{role.upper()}:")
            for cred in credentials[:3]:
                print(f"  Username: {cred['username']}")
                print(f"  Password: {cred['password']}")
                print(f"  Email: {cred['email']}")
        
        # Print shop assignments
        print("\n[Seed] Shop Assignments:")
        print("=" * 50)
        for i, shop in enumerate(shops):
            manager = users["shop_managers"][i] if i < len(users["shop_managers"]) else None
            if manager:
                print(f"  {manager.username} -> {shop.name} (ID: {shop.id})")
        
        # Print distributor partnerships
        print("\n[Seed] Distributor Partnerships:")
        print("=" * 50)
        for dist in users["distributors"]:
            partnerships_list = DistributorSupply.query.filter_by(distributor_id=dist.id, status='active').all()
            for p in partnerships_list:
                shop = Shop.query.get(p.shop_id)
                if shop:
                    print(f"  {dist.username} <-> {shop.name}")
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Seeding failed: {str(e)}"
        print(f"[Seed] {error_msg}")
        summary["errors"].append(error_msg)
        raise
    
    return summary


if __name__ == "__main__":
    # For direct execution
    from app import create_app
    app = create_app()
    
    with app.app_context():
        result = seed_comprehensive_data()
        print("\n[Seed] Seeding Summary:", result)
