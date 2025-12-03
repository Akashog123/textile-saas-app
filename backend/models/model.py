#SE-Textile-App\backend\app.py
#models\model.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event, Index, func
import os

db = SQLAlchemy()


# ============================================================================
# URL RESOLUTION HELPER
# ============================================================================

def _resolve_image_url(image_path, fallback_id=None, fallback_type="product"):
    """
    Resolve image URL to full URL for API responses.
    Inline helper to avoid circular imports with utils.image_utils.
    """
    # Lazy import Config to avoid circular imports
    from config import Config
    
    if not image_path:
        if getattr(Config, 'USE_PLACEHOLDER_IMAGES', False) and fallback_id:
            dimensions = "600x400" if fallback_type == "shop" else "400x300"
            placeholder_service = getattr(Config, 'PLACEHOLDER_IMAGE_SERVICE', 'https://placehold.co')
            return f"{placeholder_service}/{dimensions}?text={fallback_type}&seed={fallback_id}"
        return None
    
    # If already absolute URL, return as-is
    if image_path.startswith(("http://", "https://")):
        return image_path
    
    # Prepend API base URL for relative paths
    api_base = getattr(Config, 'API_BASE_URL', 'http://127.0.0.1:5001')
    if image_path.startswith("/"):
        return f"{api_base}{image_path}"
    
    # For paths without leading slash, assume uploads path
    static_path = getattr(Config, 'STATIC_IMAGE_PATH', '/uploads')
    return f"{api_base}{static_path}/{image_path}"


# ============================================================================
# UTILITY / MIXINS
# ============================================================================

class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class SerializerMixin:
    """Mixin providing standardized serialization methods."""
    
    # Define which fields to include in basic serialization (override in subclass)
    _serializable_fields = []
    _serializable_relations = {}  # {'relation_name': 'method_name'}
    
    def to_dict(self, include_relations=False):
        """Convert model to dictionary with optional relations."""
        result = {}
        for field in self._serializable_fields:
            value = getattr(self, field, None)
            if isinstance(value, datetime):
                result[field] = value.isoformat() if value else None
            elif hasattr(value, '__decimal__') or str(type(value)) == "<class 'decimal.Decimal'>":
                result[field] = float(value) if value else 0.0
            else:
                result[field] = value
        
        if include_relations and self._serializable_relations:
            for rel_name, method_name in self._serializable_relations.items():
                rel = getattr(self, rel_name, None)
                if rel is not None:
                    if callable(getattr(rel, method_name, None)):
                        result[rel_name] = getattr(rel, method_name)()
                    elif hasattr(rel, 'all'):  # Dynamic relationship
                        result[rel_name] = [getattr(item, method_name)() for item in rel.all()[:10]]
        
        return result
    
    def to_summary(self):
        """Return minimal representation for lists/references."""
        return {"id": getattr(self, 'id', None), "name": getattr(self, 'name', None)}


# ============================================================================
# USER MODEL
# ============================================================================

class User(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "users"
    
    _serializable_fields = [
        'id', 'full_name', 'username', 'email', 'role', 'contact',
        'address', 'city', 'state', 'pincode', 'avatar_url', 'bio',
        'approved', 'last_login_at', 'created_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), default="customer", nullable=False, index=True)
    contact = db.Column(db.String(30))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=True, index=True)
    last_login_at = db.Column(db.DateTime)
    primary_shop_id = db.Column(db.Integer, db.ForeignKey("shops.id", use_alter=True, name="fk_user_primary_shop"), nullable=True)

    # Relationships
    shops = db.relationship("Shop", backref="owner", lazy="dynamic", cascade="all, delete-orphan", foreign_keys="Shop.owner_id")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
    
    def to_public_dict(self):
        """Return public-safe user info (excludes password, email)."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "role": self.role,
            "city": self.city,
            "avatar_url": self.avatar_url,
            "approved": self.approved
        }
    
    def to_auth_dict(self, include_shop=False):
        """Return user info for authentication responses."""
        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "approved": self.approved,
            "primary_shop_id": self.primary_shop_id
        }
        if include_shop and self.role.lower() in ["shop_owner", "shop_manager", "admin"]:
            # Return primary shop or first shop as fallback
            primary_shop = self.get_primary_shop()
            result["shop_id"] = primary_shop.id if primary_shop else None
            result["shop_count"] = self.shops.count()
        return result
    
    def get_primary_shop(self):
        """Get the user's primary shop, or first shop as fallback."""
        if self.primary_shop_id:
            shop = Shop.query.get(self.primary_shop_id)
            if shop and shop.owner_id == self.id:
                return shop
        # Fallback to first shop
        return self.shops.first()
    
    def set_primary_shop(self, shop_id):
        """Set the primary shop for this user."""
        shop = Shop.query.get(shop_id)
        if shop and shop.owner_id == self.id:
            self.primary_shop_id = shop_id
            return True
        return False
    
    def get_all_shops_summary(self):
        """Get summary of all shops owned by user."""
        return [
            {
                "id": s.id,
                "name": s.name or "",
                "city": s.city or "",
                "is_primary": s.id == self.primary_shop_id,
                "product_count": s.products.count(),
                "rating": round(s.rating or 0.0, 1)
            }
            for s in self.shops.order_by(Shop.created_at.desc()).all()
        ]

# ============================================================================
# SHOP MODEL
# ============================================================================

class Shop(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "shops"
    
    _serializable_fields = [
        'id', 'name', 'description', 'image_url', 'address', 'city', 'state',
        'location', 'contact', 'gstin', 'lat', 'lon', 'rating', 'is_popular',
        'owner_id', 'created_at', 'updated_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100), index=True)
    state = db.Column(db.String(100))
    location = db.Column(db.String(255))
    contact = db.Column(db.String(30))
    gstin = db.Column(db.String(20))
    lat = db.Column(db.Float, index=True)
    lon = db.Column(db.Float, index=True)
    rating = db.Column(db.Float, default=0.0)
    is_popular = db.Column(db.Boolean, default=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    reviews = db.relationship("Review", backref="shop", lazy="dynamic", cascade="all, delete-orphan")
    sales_data = db.relationship("SalesData", back_populates="shop", lazy="dynamic", cascade="all, delete-orphan")
    products = db.relationship("Product", backref="shop", lazy="dynamic", cascade="all, delete-orphan")
    images = db.relationship("ShopImage", back_populates="shop", lazy="dynamic", cascade="all, delete-orphan", order_by="ShopImage.ordering")

    # Composite index for geo queries
    __table_args__ = (
        Index('idx_shop_geo', 'lat', 'lon'),
        Index('idx_shop_city_popular', 'city', 'is_popular'),
    )

    def __repr__(self):
        return f"<Shop {self.name}>"
    
    def get_primary_image_url(self, resolve=False):
        """
        Get URL of primary shop image.
        Checks image_url field first, then ShopImage table.
        
        Args:
            resolve: If True, return full resolved URL for API responses
        """
        raw_url = None
        if self.image_url:
            raw_url = self.image_url
        else:
            # Fall back to first image from ShopImage relationship
            try:
                first_image = self.images.first()
                if first_image:
                    raw_url = first_image.url
            except (AttributeError, IndexError):
                pass
        
        if resolve:
            return _resolve_image_url(raw_url, self.id, "shop")
        return raw_url
    
    def to_card_dict(self):
        """Return shop info for card/list display with resolved image URLs."""
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "rating": round(self.rating or 0.0, 1),
            "image_url": self.get_primary_image_url(resolve=True),
            "is_popular": self.is_popular,
            "location": self.location
        }
    
    def to_detail_dict(self, include_owner=False):
        """Return detailed shop info with resolved image URLs."""
        result = self.to_dict()
        result["rating"] = round(self.rating or 0.0, 1)
        result["product_count"] = self.products.count()
        result["review_count"] = self.reviews.count()
        # Resolve main image_url
        result["image_url"] = self.get_primary_image_url(resolve=True)
        if include_owner and self.owner:
            result["owner"] = self.owner.to_public_dict()
        return result

# ============================================================================
# SALE ORDER MODEL
# ============================================================================

class SaleOrder(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "sale_orders"
    
    _serializable_fields = [
        'id', 'order_number', 'customer_id', 'total_amount', 'status',
        'placed_at', 'created_at', 'updated_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(120), unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    total_amount = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(50), default="created", index=True)
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("User", backref=db.backref("orders", lazy="dynamic"))
    line_items = db.relationship("SalesLineItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SaleOrder {self.order_number} total={self.total_amount}>"
    
    def to_summary_dict(self):
        """Return order summary for lists."""
        return {
            "id": self.id,
            "order_number": self.order_number,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "status": self.status,
            "placed_at": self.placed_at.isoformat() if self.placed_at else None,
            "item_count": self.line_items.count()
        }


# ============================================================================
# SALES LINE ITEM MODEL
# ============================================================================

class SalesLineItem(db.Model, SerializerMixin):
    __tablename__ = "sales_line_items"
    
    _serializable_fields = ['id', 'order_id', 'product_id', 'quantity', 'unit_price', 'total_price']

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("sale_orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Composite index for order analytics
    __table_args__ = (
        Index('idx_line_item_order_product', 'order_id', 'product_id'),
    )

    def __repr__(self):
        return f"<SalesLineItem order={self.order_id} product={self.product_id} qty={self.quantity}>"

# ============================================================================
# PRODUCT MODEL
# ============================================================================

class Product(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "products"
    
    _serializable_fields = [
        'id', 'name', 'slug', 'sku', 'category', 'description', 'price',
        'msrp', 'badge', 'rating', 'is_trending', 'is_active', 'shop_id',
        'distributor_id', 'image_url', 'created_at', 'updated_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, index=True)
    sku = db.Column(db.String(80), unique=True, index=True)
    category = db.Column(db.String(120), index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    msrp = db.Column(db.Numeric(10, 2))
    badge = db.Column(db.String(50))
    rating = db.Column(db.Float, default=4.0)
    is_trending = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    image_url = db.Column(db.String(512))

    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    images = db.relationship("ProductImage", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    inventory = db.relationship("Inventory", uselist=False, backref="product", cascade="all, delete-orphan")
    embeddings = db.relationship("ProductEmbedding", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    sales_lines = db.relationship("SalesLineItem", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    sales_data = db.relationship("SalesData", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    distributor = db.relationship("User", foreign_keys=[distributor_id], backref="supplied_products")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_product_shop_active', 'shop_id', 'is_active'),
        Index('idx_product_category_trending', 'category', 'is_trending'),
        Index('idx_product_shop_category', 'shop_id', 'category'),
    )

    def __repr__(self):
        return f"<Product {self.name} ({self.id})>"
    
    def get_primary_image_url(self, resolve=False):
        """
        Get URL of primary product image. 
        Checks image_url field first, then ProductImage table.
        
        Args:
            resolve: If True, return full resolved URL for API responses
        """
        raw_url = None
        # First check direct image_url field (synced with first ProductImage)
        if self.image_url:
            raw_url = self.image_url
        else:
            # Fall back to first image from ProductImage relationship
            primary = self.images.filter_by(ordering=0).first()
            raw_url = primary.url if primary else None
        
        if resolve:
            return _resolve_image_url(raw_url, self.id, "product")
        return raw_url
    
    def to_card_dict(self):
        """Return product info for card/list display with resolved image URLs."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": float(self.price) if self.price else 0,
            "price_formatted": f"₹{self.price:,.0f}" if self.price else "₹0",
            "rating": round(self.rating or 4.0, 1),
            "is_trending": self.is_trending,
            "image": self.get_primary_image_url(resolve=True),
            "shop_name": self.shop.name if self.shop else None
        }
    
    def to_detail_dict(self, include_shop=True, include_inventory=True):
        """Return detailed product info with resolved image URLs."""
        result = self.to_dict()
        result["price_formatted"] = f"₹{self.price:,.0f}" if self.price else "₹0"
        result["rating"] = round(self.rating or 4.0, 1)
        result["image"] = self.get_primary_image_url(resolve=True)
        # Resolve all image URLs in the images array
        result["images"] = [
            {"url": _resolve_image_url(img.url, self.id, "product"), "alt": img.alt} 
            for img in self.images.order_by(ProductImage.ordering).limit(10)
        ]
        
        if include_shop and self.shop:
            result["shop"] = self.shop.to_card_dict()
        
        if include_inventory and self.inventory:
            result["stock"] = {
                "available": self.inventory.qty_available,
                "reserved": self.inventory.qty_reserved,
                "safety_stock": self.inventory.safety_stock
            }
        
        return result
    
    def to_inventory_dict(self):
        """Return product info for inventory management with resolved image URLs."""
        inv = self.inventory
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": float(self.price) if self.price else 0,
            "stock": inv.qty_available if inv else 0,
            "minimum_stock": inv.safety_stock if inv else 0,
            "sku": self.sku or f"AUTO-{self.id}",
            "rating": round(self.rating or 4.0, 1),
            "shop_id": self.shop_id,
            "image": self.get_primary_image_url(resolve=True),
            "images": [
                {"id": img.id, "url": _resolve_image_url(img.url, self.id, "product"), "alt": img.alt} 
                for img in self.images.order_by(ProductImage.ordering).limit(4)
            ]
        }


# ============================================================================
# SHOP IMAGE MODEL
# ============================================================================

class ShopImage(db.Model, TimestampMixin, SerializerMixin):
    """
    Model for storing multiple images per shop (up to 4 images).
    """
    __tablename__ = "shop_images"
    
    _serializable_fields = ['id', 'shop_id', 'url', 'alt', 'ordering', 'created_at']

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    url = db.Column(db.String(512), nullable=False)
    alt = db.Column(db.String(255))
    ordering = db.Column(db.Integer, default=0)  # 0-3 for up to 4 images
    
    # Relationship back to shop
    shop = db.relationship("Shop", back_populates="images")
    
    def __repr__(self):
        return f"<ShopImage {self.id} shop={self.shop_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "url": self.url,
            "alt": self.alt,
            "ordering": self.ordering,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# PRODUCT IMAGE MODEL
# ============================================================================

class ProductImage(db.Model, SerializerMixin):
    __tablename__ = "product_images"
    
    _serializable_fields = ['id', 'product_id', 'url', 'alt', 'ordering']

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    url = db.Column(db.String(512), nullable=False)
    alt = db.Column(db.String(255))
    ordering = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f"<ProductImage {self.id} product={self.product_id}>"


# ============================================================================
# PRODUCT EMBEDDING MODEL
# ============================================================================

class ProductEmbedding(db.Model):
    __tablename__ = "product_embeddings"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    vector = db.Column(db.PickleType, nullable=False)
    model = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProductEmbedding {self.id} model={self.model}>"

# ============================================================================
# INVENTORY MODEL
# ============================================================================

class Inventory(db.Model, SerializerMixin):
    __tablename__ = "inventory"
    
    _serializable_fields = [
        'id', 'product_id', 'qty_available', 'qty_reserved', 'safety_stock',
        'total_purchased', 'total_sold', 'updated_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True, index=True)
    qty_available = db.Column(db.Integer, default=0)
    qty_reserved = db.Column(db.Integer, default=0)
    safety_stock = db.Column(db.Integer, default=0)
    total_purchased = db.Column(db.Integer, default=0)
    total_sold = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Inventory product={self.product_id} qty={self.qty_available}>"
    
    @property
    def needs_reorder(self):
        """Check if product needs reordering."""
        return self.qty_available <= self.safety_stock
    
    @property
    def effective_available(self):
        """Get available quantity minus reserved."""
        return max(0, self.qty_available - self.qty_reserved)


# ============================================================================
# STOCK TRANSFER MODEL
# ============================================================================

class StockTransfer(db.Model):
    __tablename__ = "stock_transfers"

    id = db.Column(db.Integer, primary_key=True)
    from_location = db.Column(db.String(255))
    to_location = db.Column(db.String(255))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="initiated", index=True)
    initiated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<StockTransfer {self.id} status={self.status}>"

# ============================================================================
# SALES DATA MODEL
# ============================================================================

class SalesData(db.Model, SerializerMixin):
    __tablename__ = "sales_data"
    
    _serializable_fields = [
        'id', 'date', 'product_id', 'shop_id', 'region', 'fabric_type',
        'quantity_sold', 'revenue'
    ]

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True, index=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True, index=True)
    region = db.Column(db.String(120), index=True)
    fabric_type = db.Column(db.String(100))
    quantity_sold = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Numeric(12, 2), default=0)

    product = db.relationship("Product", back_populates="sales_data")
    shop = db.relationship("Shop", back_populates="sales_data")

    # Composite indexes for analytics queries
    __table_args__ = (
        Index('idx_sales_date_shop', 'date', 'shop_id'),
        Index('idx_sales_date_product', 'date', 'product_id'),
        Index('idx_sales_shop_product', 'shop_id', 'product_id'),
        Index('idx_sales_region_date', 'region', 'date'),
    )

    def __repr__(self):
        return f"<SalesData {self.date} shop={self.shop_id} product={self.product_id} qty={self.quantity_sold}>"


# ============================================================================
# PRODUCT CATALOG MODEL
# ============================================================================

class ProductCatalog(db.Model, SerializerMixin):
    __tablename__ = "product_catalog"
    
    _serializable_fields = [
        'id', 'product_id', 'product_name', 'category', 'subcategory',
        'article_type', 'color', 'gender', 'season', 'year', 'usage',
        'image_url', 'price'
    ]

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, index=True)
    product_name = db.Column(db.String(255), index=True)
    category = db.Column(db.String(100), index=True)
    subcategory = db.Column(db.String(100))
    article_type = db.Column(db.String(100))
    color = db.Column(db.String(50), index=True)
    gender = db.Column(db.String(50), index=True)
    season = db.Column(db.String(50))
    year = db.Column(db.Integer)
    usage = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    price = db.Column(db.Integer)

    # Composite indexes for filtering
    __table_args__ = (
        Index('idx_catalog_category_gender', 'category', 'gender'),
        Index('idx_catalog_color_season', 'color', 'season'),
    )

    def __repr__(self):
        return f"<ProductCatalog {self.product_id}>"

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "subcategory": self.subcategory,
            "article_type": self.article_type,
            "color": self.color,
            "gender": self.gender,
            "season": self.season,
            "year": self.year,
            "usage": self.usage,
            "image_url": self.image_url,
            "price": self.price,
        }

# ============================================================================
# REVIEW MODEL
# ============================================================================

class Review(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "reviews"
    
    _serializable_fields = [
        'id', 'user_id', 'product_id', 'shop_id', 'rating', 'title', 'body',
        'is_verified_purchase', 'created_at', 'updated_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    user_name = db.Column(db.String(150), nullable=True)   # new column
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True, index=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    
    # Relationship to user who wrote the review
    reviewer = db.relationship("User", backref=db.backref("reviews_written", lazy="dynamic"))

    # Composite indexes for review queries
    __table_args__ = (
        Index('idx_review_shop_rating', 'shop_id', 'rating'),
        Index('idx_review_product_rating', 'product_id', 'rating'),
        Index('idx_review_user_shop', 'user_id', 'shop_id'),
    )

    def __repr__(self):
        return f"<Review {self.id} rating={self.rating}>"
    
    def to_display_dict(self):
        """Return review with reviewer info for display."""
        return {
            "id": self.id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "is_verified_purchase": self.is_verified_purchase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewer": {
                "id": self.reviewer.id if self.reviewer else None,
                "name": self.reviewer.full_name if self.reviewer else "Anonymous",
                "avatar_url": self.reviewer.avatar_url if self.reviewer else None
            }
        }


# ============================================================================
# UPLOAD MODEL
# ============================================================================

class Upload(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "uploads"
    
    _serializable_fields = [
        'id', 'filename', 'original_name', 'content_type', 'size', 'url',
        'uploaded_by', 'meta_data', 'created_at'
    ]
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    content_type = db.Column(db.String(120), index=True)
    size = db.Column(db.Integer)
    url = db.Column(db.String(800), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    meta_data = db.Column(db.JSON)
    
    def __repr__(self):
        return f"<Upload {self.filename}>"


# ============================================================================
# ACTIVITY LOG MODEL
# ============================================================================

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(255), index=True)
    context = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Index for audit queries
    __table_args__ = (
        Index('idx_activity_user_action', 'user_id', 'action'),
        Index('idx_activity_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ActivityLog {self.action}>"


# ============================================================================
# FORECAST JOB MODEL
# ============================================================================

class ForecastJob(db.Model):
    __tablename__ = "forecast_jobs"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    params = db.Column(db.JSON)
    status = db.Column(db.String(80), default="pending", index=True)
    result_url = db.Column(db.String(500))
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ForecastJob {self.name} status={self.status}>"


# ============================================================================
# NOTIFICATION MODEL
# ============================================================================

class Notification(db.Model, SerializerMixin):
    __tablename__ = "notifications"
    
    _serializable_fields = ['id', 'user_id', 'title', 'message', 'link', 'is_read', 'created_at']
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    link = db.Column(db.String(512))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Composite index for user notifications
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
    )
    
    def __repr__(self):
        return f"<Notification {self.title}>"

# ============================================================================
# STORE REGION MODEL
# ============================================================================

class StoreRegion(db.Model, SerializerMixin):
    __tablename__ = 'store_regions'
    
    _serializable_fields = [
        'RegionID', 'StoreName', 'City', 'Product_description', 'Latitude',
        'Longitude', 'RegionName', 'ImagePath'
    ]

    RegionID = db.Column(db.Integer, primary_key=True)
    StoreName = db.Column(db.String(100), nullable=False, index=True)
    City = db.Column(db.String(100), nullable=False, index=True)
    Product_description = db.Column(db.String(500), nullable=False)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    RegionName = db.Column(db.String(50), nullable=False, index=True)
    ImagePath = db.Column(db.String(255), nullable=True)
    
    # Composite index for geo queries
    __table_args__ = (
        Index('idx_store_region_geo', 'Latitude', 'Longitude'),
        Index('idx_store_region_city', 'City', 'RegionName'),
    )

    def __repr__(self):
        return f"<StoreRegion {self.StoreName}>"
    
    def to_map_dict(self):
        """Return store info for map display."""
        return {
            "id": self.RegionID,
            "name": self.StoreName,
            "Latitude": self.Latitude,
            "Longitude": self.Longitude,
            "Region": self.RegionName,
            "ImagePath": self.ImagePath
        }


# ============================================================================
# EXTERNAL PRODUCT MODEL
# ============================================================================

class ExternalProduct(db.Model, SerializerMixin):
    __tablename__ = 'external_product'
    
    _serializable_fields = [
        'ID', 'ProductID', 'ProductCategory', 'Occasion', 'Material',
        'Karigari', 'Karigari_description', 'Product_description'
    ]

    ID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, unique=True, nullable=False, index=True)
    ProductCategory = db.Column(db.String(100), nullable=False, index=True)
    Occasion = db.Column(db.String(100))
    Material = db.Column(db.String(100))
    Karigari = db.Column(db.String(100))
    Karigari_description = db.Column(db.Text)
    Product_description = db.Column(db.Text)

    sales_items = db.relationship(
        'ExternalSalesDataItem',
        back_populates='product',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<ExternalProduct {self.ProductID}>"


# ============================================================================
# EXTERNAL SALES DATA ITEM MODEL
# ============================================================================

class ExternalSalesDataItem(db.Model, SerializerMixin):
    __tablename__ = 'external_sales_data_item'
    
    _serializable_fields = [
        'id', 'ProductID', 'OrderId', 'UnitsSold', 'Sales', 'SaleDate',
        'Store', 'Region'
    ]

    id = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey('external_product.ProductID'), nullable=False, index=True)
    OrderId = db.Column(db.Integer, nullable=False, index=True)
    UnitsSold = db.Column(db.Integer, nullable=False)
    Sales = db.Column(db.Float, nullable=False)
    SaleDate = db.Column(db.Date, nullable=False, index=True)
    Store = db.Column(db.String(100), nullable=False, index=True)
    Region = db.Column(db.String(50), nullable=False, index=True)

    product = db.relationship('ExternalProduct', back_populates='sales_items')
    
    # Composite indexes for analytics
    __table_args__ = (
        Index('idx_ext_sales_date_store', 'SaleDate', 'Store'),
        Index('idx_ext_sales_region_product', 'Region', 'ProductID'),
    )

    def __repr__(self):
        return f"<ExternalSalesDataItem Order={self.OrderId}, Product={self.ProductID}>"


# ============================================================================
# MARKETING HISTORY MODEL
# ============================================================================

class MarketingHistory(db.Model, SerializerMixin):
    """Track marketing content generation history"""
    __tablename__ = "marketing_history"
    
    _serializable_fields = [
        'id', 'user_id', 'file_name', 'file_type', 'content_type',
        'generated_content', 'status', 'error_message', 'rows_processed', 'created_at'
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False, index=True)  # 'csv', 'xlsx', 'image'
    content_type = db.Column(db.String(50), nullable=False, index=True)  # 'data', 'image'
    generated_content = db.Column(db.Text)  # JSON string of generated content
    status = db.Column(db.String(20), default='completed', index=True)  # 'completed', 'failed'
    error_message = db.Column(db.Text)
    rows_processed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship
    user = db.relationship("User", backref=db.backref("marketing_history", lazy="dynamic", cascade="all, delete-orphan"))
    
    # Composite index for user history queries
    __table_args__ = (
        Index('idx_marketing_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<MarketingHistory {self.file_name} ({self.content_type})>"


# ============================================================================
# INQUIRY MODEL
# ============================================================================

class Inquiry(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "inquiries"
    
    _serializable_fields = ['id', 'sender_id', 'message', 'image_url', 'created_at']

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(512))
    
    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_inquiries")
    recipients = db.relationship("InquiryRecipient", backref="inquiry", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inquiry {self.id} from {self.sender_id}>"
    
    def to_detail_dict(self, include_sender=True):
        """Return inquiry with sender info."""
        result = self.to_dict()
        result["recipient_count"] = self.recipients.count()
        if include_sender and self.sender:
            result["sender"] = self.sender.to_public_dict()
        return result


# ============================================================================
# INQUIRY RECIPIENT MODEL
# ============================================================================

class InquiryRecipient(db.Model, TimestampMixin, SerializerMixin):
    __tablename__ = "inquiry_recipients"
    
    _serializable_fields = ['id', 'inquiry_id', 'recipient_id', 'status', 'read_at', 'created_at']
    
    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey("inquiries.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(50), default="pending", index=True)  # pending, read, replied
    read_at = db.Column(db.DateTime)
    
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_inquiries")
    
    # Composite index for recipient inbox
    __table_args__ = (
        Index('idx_inquiry_recipient_status', 'recipient_id', 'status'),
    )

    def __repr__(self):
        return f"<InquiryRecipient {self.inquiry_id} -> {self.recipient_id}>"


# ============================================================================
# INQUIRY MESSAGE MODEL (Chat Messages)
# ============================================================================

class InquiryMessage(db.Model, TimestampMixin, SerializerMixin):
    """Chat messages within an inquiry thread between shop owner and distributor."""
    __tablename__ = "inquiry_messages"
    
    _serializable_fields = ['id', 'inquiry_recipient_id', 'sender_id', 'message', 'image_url', 'is_read', 'read_at', 'created_at']
    
    id = db.Column(db.Integer, primary_key=True)
    inquiry_recipient_id = db.Column(db.Integer, db.ForeignKey("inquiry_recipients.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(512))
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    inquiry_recipient = db.relationship("InquiryRecipient", backref=db.backref("messages", lazy="dynamic", cascade="all, delete-orphan"))
    
    # Index for unread messages
    __table_args__ = (
        Index('idx_inquiry_message_unread', 'inquiry_recipient_id', 'is_read'),
    )

    def __repr__(self):
        return f"<InquiryMessage {self.id} in thread {self.inquiry_recipient_id}>"
    
    def to_chat_dict(self):
        """Return message formatted for chat display."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else "Unknown",
            "sender_role": self.sender.role if self.sender else "unknown",
            "message": self.message,
            "image_url": self.image_url,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# CACHED AI INSIGHTS MODEL
# ============================================================================

class CachedAIInsight(db.Model, TimestampMixin):
    """
    Stores AI-generated insights for a shop to avoid redundant AI API calls.
    Insights are regenerated only when new sales data is uploaded.
    """
    __tablename__ = "cached_ai_insights"
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    insight_type = db.Column(db.String(50), nullable=False, index=True)  # 'dashboard', 'upload', 'summary'
    insights_json = db.Column(db.Text)  # JSON array of insights
    demand_summary = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    data_hash = db.Column(db.String(128))  # Hash of source data to detect staleness
    is_stale = db.Column(db.Boolean, default=False, index=True)
    expires_at = db.Column(db.DateTime, index=True)
    
    shop = db.relationship("Shop", backref=db.backref("cached_insights", lazy="dynamic", cascade="all, delete-orphan"))
    
    __table_args__ = (
        Index('idx_cached_insight_shop_type', 'shop_id', 'insight_type'),
        db.UniqueConstraint('shop_id', 'insight_type', name='uq_shop_insight_type'),
    )
    
    def __repr__(self):
        return f"<CachedAIInsight shop={self.shop_id} type={self.insight_type}>"
    
    def to_dict(self):
        import json
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "insight_type": self.insight_type,
            "insights": json.loads(self.insights_json) if self.insights_json else [],
            "demand_summary": self.demand_summary,
            "recommendation": self.recommendation,
            "is_stale": self.is_stale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


# ============================================================================
# CACHED FORECAST MODEL
# ============================================================================

class CachedForecast(db.Model, TimestampMixin):
    """
    Stores Prophet-generated forecasts for a shop to avoid redundant computation.
    Forecasts are regenerated only when new sales data is uploaded.
    """
    __tablename__ = "cached_forecasts"
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    forecast_type = db.Column(db.String(50), nullable=False, index=True)  # 'quarterly', 'weekly_trend', 'monthly_trend', 'yearly_trend'
    forecast_json = db.Column(db.Text)  # Full forecast response as JSON
    data_hash = db.Column(db.String(128))  # Hash of source data to detect staleness
    is_stale = db.Column(db.Boolean, default=False, index=True)
    expires_at = db.Column(db.DateTime, index=True)
    
    shop = db.relationship("Shop", backref=db.backref("cached_forecasts", lazy="dynamic", cascade="all, delete-orphan"))
    
    __table_args__ = (
        Index('idx_cached_forecast_shop_type', 'shop_id', 'forecast_type'),
        db.UniqueConstraint('shop_id', 'forecast_type', name='uq_shop_forecast_type'),
    )
    
    def __repr__(self):
        return f"<CachedForecast shop={self.shop_id} type={self.forecast_type}>"
    
    def to_dict(self):
        import json
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "forecast_type": self.forecast_type,
            "forecast": json.loads(self.forecast_json) if self.forecast_json else {},
            "is_stale": self.is_stale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


# ============================================================================
# SALES UPLOAD LOG MODEL
# ============================================================================

class SalesUploadLog(db.Model, SerializerMixin):
    """Audit trail for weekly sales uploads and SLA monitoring."""
    __tablename__ = "sales_upload_log"

    SLA_LIMIT_MS = 120000  # 2 minutes
    
    _serializable_fields = [
        'id', 'shop_id', 'file_name', 'file_hash', 'started_at', 'completed_at',
        'duration_ms', 'status', 'rows_processed', 'sla_breached', 'duplicate_of', 'message'
    ]

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(128), nullable=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime)
    duration_ms = db.Column(db.Integer)
    status = db.Column(db.String(40), default="in_progress", index=True)
    rows_processed = db.Column(db.Integer, default=0)
    sla_breached = db.Column(db.Boolean, default=False, index=True)
    duplicate_of = db.Column(db.Integer, db.ForeignKey("sales_upload_log.id"))
    message = db.Column(db.String(255))

    shop = db.relationship("Shop", backref=db.backref("sales_uploads", lazy="dynamic"))
    duplicate_parent = db.relationship("SalesUploadLog", remote_side=[id], uselist=False)
    
    # Composite indexes for monitoring
    __table_args__ = (
        Index('idx_upload_shop_status', 'shop_id', 'status'),
        Index('idx_upload_sla_status', 'sla_breached', 'status'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "rows_processed": self.rows_processed,
            "sla_breached": self.sla_breached,
            "duplicate_of": self.duplicate_of,
            "message": self.message,
            "sla_limit_ms": self.SLA_LIMIT_MS
        }

    def __repr__(self):
        return f"<SalesUploadLog shop={self.shop_id} status={self.status}>"


# ============================================================================
# DISTRIBUTOR SUPPLY MODEL
# ============================================================================

class DistributorSupply(db.Model):
    """Track which distributor supplies which products to which shops"""
    __tablename__ = "distributor_supplies"

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)
    quantity_supplied = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Numeric(10, 2))  # Price at which distributor supplied
    total_value = db.Column(db.Numeric(12, 2))  # Total value of supply
    supply_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(50), default="completed")  # pending, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    distributor = db.relationship("User", backref=db.backref("supplies_made", lazy="dynamic"))
    product = db.relationship("Product", backref=db.backref("supply_records", lazy="dynamic"))
    shop = db.relationship("Shop", backref=db.backref("supplies_received", lazy="dynamic"))

    # Composite index for common queries
    __table_args__ = (
        Index('idx_distributor_shop', 'distributor_id', 'shop_id'),
        Index('idx_distributor_product', 'distributor_id', 'product_id'),
    )

    def __repr__(self):
        return f"<DistributorSupply distributor={self.distributor_id} product={self.product_id} shop={self.shop_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "distributor_id": self.distributor_id,
            "product_id": self.product_id,
            "shop_id": self.shop_id,
            "quantity_supplied": self.quantity_supplied,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "total_value": float(self.total_value) if self.total_value else None,
            "supply_date": self.supply_date.isoformat() if self.supply_date else None,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# DB SETUP & EVENT LISTENERS
# ============================================================================

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


@event.listens_for(User, "before_insert")
def default_user_approved(mapper, connection, target):
    if target.role == "shop_owner" and target.approved is None:
        target.approved = False
