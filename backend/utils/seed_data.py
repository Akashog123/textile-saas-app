"""Minimal data seeding utilities for local testing.

This module ingests a few rows from the existing fashion dataset CSV files to
hydrate the database with realistic demo entities (user, shop, products and
store regions). The intent is to keep the seeded data lightweight so that
fresh databases have something meaningful to work with in Swagger/UX flows
without polluting production instances.
"""

from __future__ import annotations

import os
import random
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Tuple

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
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEXTILE_DIR = os.path.join(BASE_DIR, "data", "Textile-2")
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

PRODUCTS_PATH = os.path.join(TEXTILE_DIR, "products.csv")
PURCHASE_DATA_PATH = os.path.join(TEXTILE_DIR, "purchase_data.csv")
STORE_REGIONS_PATH = os.path.join(TEXTILE_DIR, "store_regions.csv")
SALES_DATA_PATH = os.path.join(TEXTILE_DIR, "sales_data.csv")
SHOP_SALES_PATH = os.path.join(INSTANCE_DIR, "sales_shop_1.csv")

MAX_PRODUCTS = 25
MAX_STORES = 7
MAX_SALES = 40
MAX_EXTERNAL_PRODUCTS = 120
MAX_EXTERNAL_SALES = 250


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _safe_read_csv(path: str, nrows: int = 40) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, nrows=nrows)
    except Exception as exc:
        print(f"[Seed] Could not read {path}: {exc}")
        return None


def _resolve_store_image(path: Any) -> str:
    if path is None or (isinstance(path, float) and pd.isna(path)):
        return ""
    normalized = str(path).strip().replace("\\", "/")
    if not normalized:
        return ""
    if normalized.startswith("http"):
        return normalized
    if normalized.startswith("/"):
        return normalized
    return f"/{normalized}"


def _ensure_demo_owner() -> tuple[User, Shop]:
    owner = User.query.filter_by(username="demo_owner").first()
    if not owner:
        owner = User(
            full_name="Demo Shop Owner",
            username="demo_owner",
            email="demo_owner@example.com",
            password=generate_password_hash("DemoPass123"),
            role="shop_owner",
            approved=True,
            city="Bengaluru",
            state="Karnataka",
        )
        db.session.add(owner)
        db.session.flush()

    shop = Shop.query.filter_by(owner_id=owner.id).first()
    if not shop:
        shop = Shop(
            name="Demo Textile Hub",
            description="Auto-seeded shop for demo logins",
            city=owner.city,
            state=owner.state,
            owner_id=owner.id,
            address="MG Road",
            lat=12.9716,
            lon=77.5946,
            is_popular=True,
        )
        db.session.add(shop)
        db.session.flush()

    return owner, shop


def _seed_store_regions() -> int:
    existing = StoreRegion.query.count()
    if existing >= MAX_STORES:
        return 0

    df = _safe_read_csv(STORE_REGIONS_PATH, nrows=MAX_STORES)
    if df is None or df.empty:
        print(f"[Seed] Skipping StoreRegion seed; dataset missing at {STORE_REGIONS_PATH}")
        return 0

    insert_rows = df.to_dict(orient="records")
    created = 0
    for idx, payload in enumerate(insert_rows):
        name = payload.get("StoreName")
        if not name or StoreRegion.query.filter_by(StoreName=name).first():
            continue
        lat = payload.get("Latitude")
        lon = payload.get("Longitude")
        region = StoreRegion(
            StoreName=name,
            City=payload.get("City"),
            Product_description=payload.get("Product_description"),
            Latitude=float(lat) if pd.notna(lat) else 0.0,
            Longitude=float(lon) if pd.notna(lon) else 0.0,
            RegionName=payload.get("RegionName", "Central"),
            ImagePath=payload.get("ImagePath", ""),
        )
        db.session.add(region)
        created += 1
        if existing + created >= MAX_STORES:
            break
    return created


def _seed_shops_from_store_regions(owner: User) -> int:
    df = _safe_read_csv(STORE_REGIONS_PATH, nrows=MAX_STORES)
    if df is None or df.empty:
        print(f"[Seed] Skipping Shop seed; dataset missing at {STORE_REGIONS_PATH}")
        return 0

    created = 0

    for _, row in df.iterrows():
        name = str(row.get("StoreName") or "").strip()
        if not name or Shop.query.filter_by(name=name).first():
            continue

        city = str(row.get("City") or "").strip()
        region = str(row.get("RegionName") or "").strip()
        description = str(row.get("Product_description") or "Trusted textile retailer.").strip()

        latitude = row.get("Latitude")
        longitude = row.get("Longitude")

        shop = Shop(
            name=name,
            description=description,
            image_url=_resolve_store_image(row.get("ImagePath")),
            address=city,
            city=city,
            state=region or owner.state or "Kerala",
            location=", ".join(filter(None, [city, region])),
            lat=float(latitude) if pd.notna(latitude) else None,
            lon=float(longitude) if pd.notna(longitude) else None,
            rating=round(random.uniform(4.0, 4.9), 1),
            is_popular=True,
            owner_id=owner.id,
        )

        db.session.add(shop)
        created += 1
        if created >= MAX_STORES:
            break

    return created


def _build_purchase_lookup() -> Dict[int, Dict[str, Any]]:
    df = _safe_read_csv(PURCHASE_DATA_PATH, nrows=400)
    if df is None or df.empty:
        return {}

    df["PurchaseDate"] = pd.to_datetime(df.get("PurchaseDate"), errors="coerce")
    df.sort_values(["Productid", "PurchaseDate"], ascending=[True, False], inplace=True)
    latest = df.dropna(subset=["Productid"]).drop_duplicates(subset=["Productid"], keep="first")

    lookup: Dict[int, Dict[str, Any]] = {}
    for _, row in latest.iterrows():
        pid = int(row.get("Productid"))
        lookup[pid] = {
            "unit_price": Decimal(str(row.get("UnitPrice", 0) or 0)),
            "inbound": int(row.get("InboundInventory", 0) or 0),
        }
    return lookup


def _seed_products(owner: User, shop: Shop) -> Dict[int, Tuple[Product, Dict[str, Any]]]:
    existing = Product.query.count()
    if existing >= MAX_PRODUCTS:
        return {}

    df = _safe_read_csv(PRODUCTS_PATH, nrows=60)
    if df is None or df.empty:
        print(f"[Seed] Skipping product seed; dataset missing at {PRODUCTS_PATH}")
        return {}

    purchase_lookup = _build_purchase_lookup()
    created_map: Dict[int, Tuple[Product, Dict[str, Any]]] = {}

    for _, row in df.iterrows():
        dataset_pid = row.get("Productid")
        if pd.isna(dataset_pid):
            continue
        dataset_pid = int(dataset_pid)
        name = str(row.get("Full_Description") or row.get("Product_description") or "").strip()
        if not name:
            continue

        slug = f"{_slugify(name)}-{dataset_pid}"
        if Product.query.filter_by(slug=slug).first():
            continue

        sku = f"SKU-{dataset_pid}"
        purchase_meta = purchase_lookup.get(dataset_pid, {})
        price_val = purchase_meta.get("unit_price") or Decimal(random.randint(5000, 20000))

        product = Product(
            name=name,
            slug=slug,
            sku=sku,
            category=row.get("ProductCategory"),
            description=row.get("Product_description") or row.get("Karigari_description"),
            price=price_val,
            msrp=price_val * Decimal("1.1"),
            badge=row.get("Occasion"),
            rating=4.2,
            is_trending=False,
            is_active=True,
            shop_id=shop.id,
            seller_id=owner.id,
        )
        db.session.add(product)
        db.session.flush()

        inventory_qty = purchase_meta.get("inbound") or random.randint(15, 60)
        inventory = Inventory(
            product_id=product.id,
            qty_available=inventory_qty,
            qty_reserved=0,
            safety_stock=max(5, int(inventory_qty * 0.1)),
        )
        db.session.add(inventory)

        created_map[dataset_pid] = (product, {
            "material": row.get("Material"),
            "category": row.get("ProductCategory"),
        })

        if existing + len(created_map) >= MAX_PRODUCTS:
            break

    return created_map


def _seed_sales_data(shop: Shop, product_lookup: Dict[int, Tuple[Product, Dict[str, Any]]]) -> int:
    existing = SalesData.query.count()
    if existing >= MAX_SALES:
        return 0

    created = 0
    sales_payloads = []
    month_start = datetime.utcnow().date().replace(day=1)
    has_recent_sales = SalesData.query.filter(SalesData.date >= month_start).count() > 0

    sales_df = _safe_read_csv(SALES_DATA_PATH, nrows=200)
    if sales_df is not None and not sales_df.empty:
        sales_df["SaleDate"] = pd.to_datetime(sales_df.get("SaleDate"), errors="coerce")
        for _, row in sales_df.iterrows():
            pid = row.get("Productid")
            if pd.isna(pid):
                continue
            pid = int(pid)
            product_meta = product_lookup.get(pid)
            if not product_meta:
                continue

            sales_payloads.append({
                "date": row.get("SaleDate"),
                "product_id": product_meta[0].id,
                "region": row.get("Region"),
                "fabric_type": product_meta[1].get("material"),
                "qty": int(row.get("UnitsSold", 0) or 0),
                "revenue": Decimal(str(row.get("Sales", 0) or 0)),
            })

    shop_sales_df = _safe_read_csv(SHOP_SALES_PATH, nrows=60)
    if shop_sales_df is not None and not shop_sales_df.empty:
        shop_sales_df["date"] = pd.to_datetime(shop_sales_df.get("date"), errors="coerce")
        for _, row in shop_sales_df.iterrows():
            sales_payloads.append({
                "date": row.get("date"),
                "product_id": None,
                "region": row.get("region"),
                "fabric_type": row.get("fabric_type"),
                "qty": int(row.get("quantity_sold", 0) or 0),
                "revenue": Decimal(str(row.get("revenue", 0) or 0)),
            })

    for payload in sales_payloads:
        if existing + created >= MAX_SALES:
            break
        if pd.isna(payload["date"]):
            continue

        entry = SalesData(
            date=pd.to_datetime(payload["date"]).date(),
            product_id=payload["product_id"],
            shop_id=shop.id,
            region=payload.get("region"),
            fabric_type=payload.get("fabric_type"),
            quantity_sold=payload.get("qty", 0),
            revenue=payload.get("revenue", Decimal(0)),
        )
        db.session.add(entry)
        created += 1
        if not has_recent_sales and entry.date >= month_start:
            has_recent_sales = True

    if not has_recent_sales and product_lookup:
        recent_entries = []
        available_products = list(product_lookup.values())
        random.shuffle(available_products)
        for idx, (product, meta) in enumerate(available_products):
            if existing + created + len(recent_entries) >= MAX_SALES or idx >= 5:
                break
            seed_date = month_start + timedelta(days=min(idx * 3, 27))
            recent_entries.append(SalesData(
                date=seed_date,
                product_id=product.id,
                shop_id=shop.id,
                region=meta.get("category") or "Central",
                fabric_type=meta.get("material"),
                quantity_sold=random.randint(6, 18),
                revenue=Decimal(random.randint(9000, 18000)),
            ))

        for entry in recent_entries:
            db.session.add(entry)
            created += 1
        if recent_entries:
            has_recent_sales = True

    return created


def _seed_external_products() -> int:
    existing_count = ExternalProduct.query.count()
    if existing_count >= MAX_EXTERNAL_PRODUCTS:
        return 0

    df = _safe_read_csv(PRODUCTS_PATH, nrows=400)
    if df is None or df.empty:
        print(f"[Seed] Skipping external_product seed; dataset missing at {PRODUCTS_PATH}")
        return 0

    existing_ids = {
        pid for (pid,) in db.session.query(ExternalProduct.ProductID).all()
    }

    created = 0
    for _, row in df.iterrows():
        dataset_pid = row.get("Productid")
        if pd.isna(dataset_pid):
            continue
        dataset_pid = int(dataset_pid)
        if dataset_pid in existing_ids:
            continue

        product = ExternalProduct(
            ProductID=dataset_pid,
            ProductCategory=row.get("ProductCategory") or "General",
            Occasion=row.get("Occasion"),
            Material=row.get("Material"),
            Karigari=row.get("Karigari"),
            Karigari_description=row.get("Karigari_description"),
            Product_description=row.get("Product_description"),
        )
        db.session.add(product)
        existing_ids.add(dataset_pid)
        created += 1

        if existing_count + created >= MAX_EXTERNAL_PRODUCTS:
            break

    return created


def _seed_external_sales_data() -> int:
    existing_count = ExternalSalesDataItem.query.count()
    if existing_count >= MAX_EXTERNAL_SALES:
        return 0

    df = _safe_read_csv(SALES_DATA_PATH, nrows=500)
    if df is None or df.empty:
        print(f"[Seed] Skipping external_sales_data seed; dataset missing at {SALES_DATA_PATH}")
        return 0

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

    created = 0
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
            Store=row.get("Store") or "Unknown",
            Region=row.get("Region") or "Unknown",
        )

        db.session.add(sale_entry)
        existing_pairs.add(key)
        created += 1

        if existing_count + created >= MAX_EXTERNAL_SALES:
            break

    return created


def seed_minimal_data() -> Dict[str, Any]:
    """Seed a tiny slice of demo data for local testing using Textile datasets."""

    summary = {
        "users": 0,
        "shops": 0,
        "products": 0,
        "stores": 0,
        "sales": 0,
        "external_products": 0,
        "external_sales": 0,
    }
    owner_before = User.query.filter_by(username="demo_owner").first()
    shop_before = None
    if owner_before:
        shop_before = Shop.query.filter_by(owner_id=owner_before.id).first()

    owner, shop = _ensure_demo_owner()
    if not owner_before:
        summary["users"] = 1
    if not shop_before:
        summary["shops"] = 1

    summary["stores"] = _seed_store_regions()
    summary["shops"] += _seed_shops_from_store_regions(owner)
    product_map = _seed_products(owner, shop)
    summary["products"] = len(product_map)
    summary["sales"] = _seed_sales_data(shop, product_map)
    summary["external_products"] = _seed_external_products()
    summary["external_sales"] = _seed_external_sales_data()

    db.session.commit()
    return summary
