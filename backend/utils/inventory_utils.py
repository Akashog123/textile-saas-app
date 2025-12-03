from sqlalchemy import inspect, text

from models.model import db

_schema_checked = False
_product_schema_checked = False


def ensure_inventory_tracking_columns():
    """Ensure inventory table has purchase/sold tracking columns."""
    global _schema_checked
    if _schema_checked:
        return

    try:
        inspector = inspect(db.engine)
        columns = {col["name"] for col in inspector.get_columns("inventory")}
        statements = []

        if "total_purchased" not in columns:
            statements.append(text("ALTER TABLE inventory ADD COLUMN total_purchased INTEGER DEFAULT 0"))
        if "total_sold" not in columns:
            statements.append(text("ALTER TABLE inventory ADD COLUMN total_sold INTEGER DEFAULT 0"))

        if statements:
            with db.engine.begin() as conn:
                for stmt in statements:
                    conn.execute(stmt)

        _schema_checked = True
    except Exception as exc:
        # Do not block requests; just log so we can inspect
        print(f"[Inventory Schema Ensure] {exc}")


def ensure_product_image_url_column():
    """Ensure products table has image_url column for storing primary image reference."""
    global _product_schema_checked
    if _product_schema_checked:
        return

    try:
        inspector = inspect(db.engine)
        columns = {col["name"] for col in inspector.get_columns("products")}
        
        if "image_url" not in columns:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(512)"))
            print("[Product Schema] Added image_url column to products table")
        
        _product_schema_checked = True
    except Exception as exc:
        # Do not block requests; just log so we can inspect
        print(f"[Product Schema Ensure] {exc}")
