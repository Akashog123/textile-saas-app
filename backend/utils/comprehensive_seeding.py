"""
Comprehensive Role-Based Data Seeding for SE Textile App

This script creates proper user relationships and assigns data to specific users:
- Creates Customer, Shop Manager, and Distributor accounts
- Assigns shops to shop managers
- Assigns products to specific shops
- Creates sales data for specific shops
- Ensures all data has proper user relationships
"""

import os
import random
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Tuple

import pandas as pd
from werkzeug.security import generate_password_hash

from models.model import (
    db,
    User,
    Shop,
    Product,
    Inventory,
    StoreRegion,
    SalesData,
    ExternalProduct,
    ExternalSalesDataItem,
    ProductImage,
    Review,
    SaleOrder,
    SalesLineItem,
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEXTILE_DIR = os.path.join(BASE_DIR, "data", "Textile-2")
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

PRODUCTS_PATH = os.path.join(TEXTILE_DIR, "products.csv")
PURCHASE_DATA_PATH = os.path.join(TEXTILE_DIR, "purchase_data.csv")
STORE_REGIONS_PATH = os.path.join(TEXTILE_DIR, "store_regions.csv")
SALES_DATA_PATH = os.path.join(TEXTILE_DIR, "sales_data")

# Seeding limits
MAX_CUSTOMERS = 3
MAX_SHOP_MANAGERS = 3
MAX_DISTRIBUTORS = 2
MAX_SHOPS_PER_MANAGER = 1  
MAX_PRODUCTS_PER_SHOP = 20  
MAX_SALES_PER_SHOP = 25
MAX_STORE_REGIONS = 10
MAX_IMAGES_PER_PRODUCT = 3
MAX_REVIEWS_PER_PRODUCT = 5
MAX_EXTERNAL_PRODUCTS = 50
MAX_EXTERNAL_SALES = 100

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

SHOP_DATA = [
    {
        "name": "Royal Silk Emporium",
        "description": "Premium silk sarees and traditional wear",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Zaveri Bazaar, Mumbai",
        "lat": 19.0760,
        "lon": 72.8777,
        "specialties": ["Silk", "Sarees", "Traditional"]
    },
    {
        "name": "Fashion Hub Textiles",
        "description": "Modern and contemporary textile collections",
        "city": "Delhi", 
        "state": "Delhi",
        "address": "Chandni Chowk, Delhi",
        "lat": 28.7041,
        "lon": 77.1025,
        "specialties": ["Cotton", "Modern", "Casual"]
    },
    {
        "name": "Heritage Weaves",
        "description": "Handloom and artisanal textile treasures",
        "city": "Jaipur",
        "state": "Rajasthan", 
        "address": "Johari Bazaar, Jaipur",
        "lat": 26.9124,
        "lon": 75.7873,
        "specialties": ["Handloom", "Artisanal", "Traditional"]
    },
    {
        "name": "Coastal Collections",
        "description": "Beach and summer wear specialists",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "T. Nagar, Chennai", 
        "lat": 13.0827,
        "lon": 80.2707,
        "specialties": ["Cotton", "Summer", "Casual"]
    },
    {
        "name": "Bengal Textiles",
        "description": "Bengal cotton and traditional fabrics",
        "city": "Kolkata",
        "state": "West Bengal",
        "address": "Gariahat Market, Kolkata",
        "lat": 22.5726,
        "lon": 88.3639,
        "specialties": ["Cotton", "Bengal", "Traditional"]
    },
    {
        "name": "Kashmir Weaves",
        "description": "Authentic Kashmiri textiles and pashmina",
        "city": "Srinagar",
        "state": "Jammu & Kashmir",
        "address": "Lal Chowk, Srinagar",
        "lat": 34.0837,
        "lon": 74.7973,
        "specialties": ["Pashmina", "Wool", "Luxury"]
    }
]

def _slugify(value: str) -> str:
    """Convert string to slug format."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")

def _safe_read_csv(path: str, nrows: int = 50) -> pd.DataFrame | None:
    """Safely read CSV file."""
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, nrows=nrows)
    except Exception as exc:
        print(f"[Seed] Could not read {path}: {exc}")
        return None

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
    
    # Create shop managers
    for i, cred in enumerate(USER_CREDENTIALS["shop_managers"][:MAX_SHOP_MANAGERS]):
        user = User.query.filter_by(username=cred["username"]).first()
        if not user:
            user = User(
                full_name=f"Shop Owner {i+1}",
                username=cred["username"],
                email=cred["email"],
                password=generate_password_hash(cred["password"]),
                role="shop_owner",
                approved=True,
                city=SHOP_DATA[i]["city"],
                state=SHOP_DATA[i]["state"],
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

def create_store_regions() -> List[StoreRegion]:
    """Create store regions for location-based features."""
    created_regions = []
    
    df = _safe_read_csv(STORE_REGIONS_PATH, nrows=MAX_STORE_REGIONS)
    if df is None or df.empty:
        print("[Seed] No store regions data available, creating default regions")
        # Create default regions if CSV is not available
        default_regions = [
            {
                "StoreName": "Central Market",
                "City": "Mumbai",
                "Product_description": "Traditional textiles and modern fabrics",
                "Latitude": 19.0760,
                "Longitude": 72.8777,
                "RegionName": "West",
                "ImagePath": ""
            },
            {
                "StoreName": "Fashion District",
                "City": "Delhi",
                "Product_description": "Contemporary clothing and accessories",
                "Latitude": 28.7041,
                "Longitude": 77.1025,
                "RegionName": "North",
                "ImagePath": ""
            },
            {
                "StoreName": "Heritage Quarter",
                "City": "Jaipur",
                "Product_description": "Handloom and artisanal textiles",
                "Latitude": 26.9124,
                "Longitude": 75.7873,
                "RegionName": "West",
                "ImagePath": ""
            }
        ]
        
        for region_data in default_regions:
            existing = StoreRegion.query.filter_by(StoreName=region_data["StoreName"]).first()
            if not existing:
                region = StoreRegion(
                    StoreName=region_data["StoreName"],
                    City=region_data["City"],
                    Product_description=region_data["Product_description"],
                    Latitude=region_data["Latitude"],
                    Longitude=region_data["Longitude"],
                    RegionName=region_data["RegionName"],
                    ImagePath=region_data["ImagePath"]
                )
                db.session.add(region)
                db.session.flush()
                created_regions.append(region)
    else:
        # Use CSV data
        for _, row in df.iterrows():
            name = str(row.get("StoreName", "")).strip()
            if not name:
                continue
                
            existing = StoreRegion.query.filter_by(StoreName=name).first()
            if existing:
                created_regions.append(existing)
                continue
                
            region = StoreRegion(
                StoreName=name,
                City=str(row.get("City", "")).strip(),
                Product_description=str(row.get("Product_description", "")).strip(),
                Latitude=float(row.get("Latitude", 0)) if pd.notna(row.get("Latitude")) else 0.0,
                Longitude=float(row.get("Longitude", 0)) if pd.notna(row.get("Longitude")) else 0.0,
                RegionName=str(row.get("RegionName", "Central")).strip(),
                ImagePath=str(row.get("ImagePath", "")).strip()
            )
            db.session.add(region)
            db.session.flush()
            created_regions.append(region)
    
    return created_regions

def create_product_images(shop_products: Dict[int, List[Product]]) -> List[ProductImage]:
    """Create product images for all products."""
    created_images = []
    
    # Sample image URLs (could be replaced with actual image URLs)
    sample_image_urls = [
        "https://images.unsplash.com/photo-1524750535607-46bd9a9c5d8a?w=400",
        "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400", 
        "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=400",
        "https://images.unsplash.com/photo-1506675420520-13e2856fc846?w=400",
        "https://images.unsplash.com/photo-1578632292385-fd2c9e1bd95d?w=400"
    ]
    
    for products in shop_products.values():
        for product in products:
            # Create 1-3 images per product
            num_images = random.randint(1, MAX_IMAGES_PER_PRODUCT)
            
            for i in range(num_images):
                existing = ProductImage.query.filter_by(
                    product_id=product.id, 
                    ordering=i
                ).first()
                
                if existing:
                    created_images.append(existing)
                    continue
                
                image = ProductImage(
                    product_id=product.id,
                    url=random.choice(sample_image_urls),
                    alt=f"{product.name} - Image {i+1}",
                    ordering=i
                )
                db.session.add(image)
                db.session.flush()
                created_images.append(image)
    
    return created_images

def create_product_reviews(shop_products: Dict[int, List[Product]], customers: List[User]) -> List[Review]:
    """Create reviews for products."""
    created_reviews = []
    
    review_templates = [
        "Excellent quality! Very satisfied with this purchase.",
        "Good value for money. Would recommend to others.",
        "Amazing product! Exactly as described in the photos.",
        "Fast shipping and great customer service.",
        "Beautiful design and comfortable to wear.",
        "Highly recommended! Will buy again.",
        "Perfect fit and great material quality.",
        "Outstanding craftsmanship. Worth every penny!"
    ]
    
    for products in shop_products.values():
        for product in products:
            # Create 1-5 reviews per product
            num_reviews = random.randint(1, MAX_REVIEWS_PER_PRODUCT)
            
            for i in range(num_reviews):
                # Random customer for the review
                customer = random.choice(customers)
                
                # Check if review already exists
                existing = Review.query.filter_by(
                    user_id=customer.id,
                    product_id=product.id
                ).first()
                
                if existing:
                    created_reviews.append(existing)
                    continue
                
                review = Review(
                    user_id=customer.id,
                    product_id=product.id,
                    rating=random.randint(4, 5),  # Mostly positive reviews
                    title=f"Great Product!",
                    body=random.choice(review_templates),
                    is_verified_purchase=True
                )
                db.session.add(review)
                db.session.flush()
                created_reviews.append(review)
    
    return created_reviews

def create_external_products() -> List[ExternalProduct]:
    """Create external products for market comparison."""
    created_products = []
    
    df = _safe_read_csv(PRODUCTS_PATH, nrows=MAX_EXTERNAL_PRODUCTS)
    if df is None or df.empty:
        print("[Seed] No external product data available")
        return created_products
    
    existing_ids = {
        pid for (pid,) in db.session.query(ExternalProduct.ProductID).all()
    }
    
    for _, row in df.iterrows():
        dataset_pid = row.get("Productid")
        if pd.isna(dataset_pid):
            continue
        dataset_pid = int(dataset_pid)
        
        if dataset_pid in existing_ids:
            continue
        
        product = ExternalProduct(
            ProductID=dataset_pid,
            ProductCategory=str(row.get("ProductCategory", "General")).strip(),
            Occasion=str(row.get("Occasion", "")).strip(),
            Material=str(row.get("Material", "")).strip(),
            Karigari=str(row.get("Karigari", "")).strip(),
            Karigari_description=str(row.get("Karigari_description", "")).strip(),
            Product_description=str(row.get("Product_description", "")).strip()
        )
        db.session.add(product)
        existing_ids.add(dataset_pid)
        created_products.append(product)
    
    return created_products

def create_external_sales_data() -> List[ExternalSalesDataItem]:
    """Create external sales data for market analytics."""
    created_sales = []
    
    df = _safe_read_csv(SALES_DATA_PATH, nrows=MAX_EXTERNAL_SALES)
    if df is None or df.empty:
        print("[Seed] No external sales data available")
        return created_sales
    
    df["SaleDate"] = pd.to_datetime(df.get("SaleDate"), errors="coerce")
    df.dropna(subset=["SaleDate"], inplace=True)
    
    existing_pairs = {
        (item.ProductID, item.OrderId)
        for item in ExternalSalesDataItem.query.with_entities(
            ExternalSalesDataItem.ProductID, ExternalSalesDataItem.OrderId
        )
    }
    
    known_products = {
        pid for (pid,) in db.session.query(ExternalProduct.ProductID).all()
    }
    
    for _, row in df.iterrows():
        product_id = row.get("Productid")
        order_id = row.get("OrderId")
        
        if pd.isna(product_id) or pd.isna(order_id):
            continue
        
        product_id = int(product_id)
        order_id = int(order_id)
        
        if product_id not in known_products:
            continue
        
        key = (product_id, order_id)
        if key in existing_pairs:
            continue
        
        sale_entry = ExternalSalesDataItem(
            ProductID=product_id,
            OrderId=order_id,
            UnitsSold=int(row.get("UnitsSold", 0) or 0),
            Sales=float(row.get("Sales", 0) or 0),
            SaleDate=pd.to_datetime(row.get("SaleDate"), errors="coerce").date(),
            Store=str(row.get("Store", "Unknown")).strip(),
            Region=str(row.get("Region", "Unknown")).strip()
        )
        
        db.session.add(sale_entry)
        existing_pairs.add(key)
        created_sales.append(sale_entry)
    
    return created_sales

def create_shops_for_managers(shop_managers: List[User]) -> List[Shop]:
    """Create shops assigned to specific shop managers - one shop per manager."""
    created_shops = []
    
    for i, manager in enumerate(shop_managers):
        # Create only one shop per manager
        if i >= len(SHOP_DATA):
            break
            
        shop_data = SHOP_DATA[i]
        
        existing_shop = Shop.query.filter_by(name=shop_data["name"]).first()
        if existing_shop:
            created_shops.append(existing_shop)
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
            rating=round(random.uniform(4.0, 4.9), 1),
            is_popular=random.choice([True, False]),
            owner_id=manager.id
        )
        db.session.add(shop)
        db.session.flush()
        created_shops.append(shop)
    
    return created_shops

def create_products_for_shops(shops: List[Shop]) -> Dict[int, List[Product]]:
    """Create products assigned to specific shops."""
    df = _safe_read_csv(PRODUCTS_PATH, nrows=100)
    if df is None or df.empty:
        print("[Seed] No product data available")
        return {}
    
    shop_products = {}
    
    for shop in shops:
        shop_products[shop.id] = []
        
        # Create products for this shop
        for i in range(MAX_PRODUCTS_PER_SHOP):
            if i >= len(df):
                break
                
            row = df.iloc[i]
            product_name = str(row.get("Full_Description") or row.get("Product_description") or f"Product {i+1}").strip()
            
            if not product_name:
                continue
                
            slug = f"{_slugify(product_name)}-{shop.id}-{i}"
            
            # Check if product already exists
            existing_product = Product.query.filter_by(slug=slug).first()
            if existing_product:
                shop_products[shop.id].append(existing_product)
                continue
            
            price = Decimal(str(row.get("UnitPrice", random.randint(5000, 25000))))
            
            product = Product(
                name=product_name,
                slug=slug,
                sku=f"SKU-{shop.id}-{i+1}",
                category=row.get("ProductCategory", "General"),
                description=row.get("Product_description", f"Quality product from {shop.name}"),
                price=price,
                msrp=price * Decimal("1.2"),
                badge=row.get("Occasion", "Regular"),
                rating=round(random.uniform(4.0, 4.8), 1),
                is_trending=random.choice([True, False]),
                is_active=True,
                shop_id=shop.id,
                seller_id=shop.owner_id
            )
            db.session.add(product)
            db.session.flush()
            
            # Create inventory
            inventory = Inventory(
                product_id=product.id,
                qty_available=random.randint(10, 100),
                qty_reserved=0,
                safety_stock=random.randint(5, 20)
            )
            db.session.add(inventory)
            
            shop_products[shop.id].append(product)
    
    return shop_products

def create_sales_data_for_shops(shops: List[Shop], shop_products: Dict[int, List[Product]]) -> List[SalesData]:
    """Create sales data for specific shops and their products."""
    sales_data = []
    df = _safe_read_csv(SALES_DATA_PATH, nrows=100)
    
    for shop in shops:
        products = shop_products.get(shop.id, [])
        if not products:
            continue
            
        # Create sales records for this shop
        for i in range(MAX_SALES_PER_SHOP):
            # Random date in last 6 months
            days_ago = random.randint(0, 180)
            sale_date = datetime.utcnow().date() - timedelta(days=days_ago)
            
            # Random product from this shop
            product = random.choice(products)
            
            # Random sales data
            quantity = random.randint(1, 10)
            unit_price = product.price * Decimal(str(random.uniform(0.9, 1.1)))
            revenue = quantity * unit_price
            
            # Get region from CSV if available, otherwise use shop location
            region = shop.city
            if df is not None and not df.empty and i < len(df):
                csv_region = df.iloc[i].get("Region")
                if pd.notna(csv_region):
                    region = str(csv_region)
            
            sale = SalesData(
                date=sale_date,
                product_id=product.id,
                shop_id=shop.id,
                region=region,
                fabric_type=product.category,
                quantity_sold=quantity,
                revenue=revenue
            )
            db.session.add(sale)
            sales_data.append(sale)
    
    return sales_data

def create_customer_orders(customers: List[User], shop_products: Dict[int, List[Product]]) -> None:
    """Create sample orders for customers."""
    from models.model import SaleOrder, SalesLineItem
    
    # Flatten all products from all shops
    all_products = []
    for products in shop_products.values():
        all_products.extend(products)
    
    if not all_products:
        return
    
    for customer in customers:
        # Create 2-3 orders per customer
        for i in range(random.randint(2, 4)):
            # Random order date
            days_ago = random.randint(1, 90)
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Select 1-3 random products
            order_products = random.sample(all_products, random.randint(1, min(3, len(all_products))))
            
            # Calculate total
            total_amount = sum(p.price * random.randint(1, 3) for p in order_products)
            
            # Create order
            order = SaleOrder(
                order_number=f"ORD-{customer.id}-{i+1}-{int(order_date.timestamp())}",
                customer_id=customer.id,
                total_amount=total_amount,
                status=random.choice(["created", "confirmed", "shipped", "delivered"]),
                placed_at=order_date
            )
            db.session.add(order)
            db.session.flush()
            
            # Create line items
            for product in order_products:
                quantity = random.randint(1, 3)
                unit_price = product.price
                total_price = unit_price * quantity
                
                line_item = SalesLineItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                db.session.add(line_item)

def seed_comprehensive_data() -> Dict[str, Any]:
    """Main seeding function with proper user relationships."""
    print("[Seed] Starting comprehensive role-based data seeding...")
    
    summary = {
        "users_created": 0,
        "shops_created": 0,
        "products_created": 0,
        "sales_created": 0,
        "orders_created": 0,
        "store_regions_created": 0,
        "product_images_created": 0,
        "reviews_created": 0,
        "external_products_created": 0,
        "external_sales_created": 0,
        "errors": []
    }
    
    try:
        # 1. Create store regions
        print("[Seed] Creating store regions...")
        store_regions = create_store_regions()
        summary["store_regions_created"] = len(store_regions)
        
        # 2. Create users
        print("[Seed] Creating users...")
        users = create_users()
        summary["users_created"] = len(users["customers"]) + len(users["shop_managers"]) + len(users["distributors"])
        
        # 3. Create shops for shop managers
        print("[Seed] Creating shops for managers...")
        shops = create_shops_for_managers(users["shop_managers"])
        summary["shops_created"] = len(shops)
        
        # 4. Create products for shops
        print("[Seed] Creating products for shops...")
        shop_products = create_products_for_shops(shops)
        total_products = sum(len(products) for products in shop_products.values())
        summary["products_created"] = total_products
        
        # 5. Create product images
        print("[Seed] Creating product images...")
        product_images = create_product_images(shop_products)
        summary["product_images_created"] = len(product_images)
        
        # 6. Create product reviews
        print("[Seed] Creating product reviews...")
        product_reviews = create_product_reviews(shop_products, users["customers"])
        summary["reviews_created"] = len(product_reviews)
        
        # 7. Create sales data
        print("[Seed] Creating sales data...")
        sales_records = create_sales_data_for_shops(shops, shop_products)
        summary["sales_created"] = len(sales_records)
        
        # 8. Create customer orders
        print("[Seed] Creating customer orders...")
        create_customer_orders(users["customers"], shop_products)
        summary["orders_created"] = 1  # Will be updated by actual count
        
        # 9. Create external products
        print("[Seed] Creating external products...")
        external_products = create_external_products()
        summary["external_products_created"] = len(external_products)
        
        # 10. Create external sales data
        print("[Seed] Creating external sales data...")
        external_sales = create_external_sales_data()
        summary["external_sales_created"] = len(external_sales)
        
        # Commit all changes
        db.session.commit()
        
        print("[Seed] Comprehensive seeding completed successfully!")
        print(f"[Seed] Created: {summary['users_created']} users, {summary['shops_created']} shops, {summary['products_created']} products, {summary['sales_created']} sales records")
        print(f"[Seed] Additional: {summary['store_regions_created']} regions, {summary['product_images_created']} images, {summary['reviews_created']} reviews")
        print(f"[Seed] External: {summary['external_products_created']} external products, {summary['external_sales_created']} external sales")
        
        # Print login credentials
        print("\n[Seed] Login Credentials:")
        print("=" * 50)
        for role, credentials in USER_CREDENTIALS.items():
            print(f"\n{role.upper()}:")
            for cred in credentials[:3]:  # Show first 3 of each role
                print(f"  Username: {cred['username']}")
                print(f"  Password: {cred['password']}")
                print(f"  Email: {cred['email']}")
        
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
