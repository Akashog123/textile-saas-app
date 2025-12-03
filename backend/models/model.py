from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event, Index, func

db = SQLAlchemy()


# Utility / mixins
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), default="customer", nullable=False)
    contact = db.Column(db.String(30))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=True, index=True)
    last_login_at = db.Column(db.DateTime)

    # Relationships
    shops = db.relationship("Shop", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Shop(db.Model, TimestampMixin):
    __tablename__ = "shops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    location = db.Column(db.String(255))
    lat = db.Column(db.Float, index=True)
    lon = db.Column(db.Float, index=True)
    rating = db.Column(db.Float, default=4.0)
    is_popular = db.Column(db.Boolean, default=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    reviews = db.relationship("Review", backref="shop", lazy="dynamic", cascade="all, delete-orphan")
    sales_data = db.relationship("SalesData", back_populates="shop", lazy="dynamic", cascade="all, delete-orphan")
    products = db.relationship("Product", backref="shop", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shop {self.name}>"

class SaleOrder(db.Model, TimestampMixin):
    __tablename__ = "sale_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(120), unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    total_amount = db.Column(db.Numeric(12, 2))
    status = db.Column(db.String(50), default="created")
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("User", backref=db.backref("orders", lazy="dynamic"))
    line_items = db.relationship("SalesLineItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SaleOrder {self.order_number} total={self.total_amount}>"


class SalesLineItem(db.Model):
    __tablename__ = "sales_line_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("sale_orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)

    def __repr__(self):
        return f"<SalesLineItem order={self.order_id} product={self.product_id} qty={self.quantity}>"

class Product(db.Model, TimestampMixin):
    __tablename__ = "products"

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

    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False, index=True)

    images = db.relationship("ProductImage", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    inventory = db.relationship("Inventory", uselist=False, backref="product", cascade="all, delete-orphan")
    embeddings = db.relationship("ProductEmbedding", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    sales_lines = db.relationship("SalesLineItem", backref="product", lazy="dynamic", cascade="all, delete-orphan")
    sales_data = db.relationship("SalesData", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name} ({self.id})>"


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    url = db.Column(db.String(512), nullable=False)
    alt = db.Column(db.String(255))
    ordering = db.Column(db.Integer, default=0)


class ProductEmbedding(db.Model):
    __tablename__ = "product_embeddings"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    vector = db.Column(db.PickleType, nullable=False)
    model = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True, index=True)
    qty_available = db.Column(db.Integer, default=0)
    qty_reserved = db.Column(db.Integer, default=0)
    safety_stock = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockTransfer(db.Model):
    __tablename__ = "stock_transfers"

    id = db.Column(db.Integer, primary_key=True)
    from_location = db.Column(db.String(255))
    to_location = db.Column(db.String(255))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="initiated")
    initiated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SalesData(db.Model):
    __tablename__ = "sales_data"

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

    def __repr__(self):
        return f"<SalesData {self.date} shop={self.shop_id} product={self.product_id} qty={self.quantity_sold}>"


class ProductCatalog(db.Model):
    __tablename__ = "product_catalog"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, index=True)
    product_name = db.Column(db.String(255))
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))
    article_type = db.Column(db.String(100))
    color = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    season = db.Column(db.String(50))
    year = db.Column(db.Integer)
    usage = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    price = db.Column(db.Integer)


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

class Review(db.Model, TimestampMixin):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True, index=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)


class Upload(db.Model, TimestampMixin):
    __tablename__ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    content_type = db.Column(db.String(120))
    size = db.Column(db.Integer)
    url = db.Column(db.String(800), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    meta_data = db.Column(db.JSON)


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255))
    context = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ForecastJob(db.Model):
    __tablename__ = "forecast_jobs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    params = db.Column(db.JSON)
    status = db.Column(db.String(80), default="pending")
    result_url = db.Column(db.String(500))
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255))
    message = db.Column(db.Text)
    link = db.Column(db.String(512))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StoreRegion(db.Model):
    __tablename__ = 'store_regions'

    RegionID = db.Column(db.Integer, primary_key=True)
    StoreName = db.Column(db.String(100), nullable=False)
    City = db.Column(db.String(100), nullable=False)
    Product_description = db.Column(db.String(500), nullable=False)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    RegionName = db.Column(db.String(50), nullable=False)
    ImagePath = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<StoreRegion {self.StoreName}>"


class ExternalProduct(db.Model):
    __tablename__ = 'external_product'

    ID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, unique=True, nullable=False)
    ProductCategory = db.Column(db.String(100), nullable=False)
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


class ExternalSalesDataItem(db.Model):
    __tablename__ = 'external_sales_data_item'

    id = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey('external_product.ProductID'), nullable=False)
    OrderId = db.Column(db.Integer, nullable=False)
    UnitsSold = db.Column(db.Integer, nullable=False)
    Sales = db.Column(db.Float, nullable=False)
    SaleDate = db.Column(db.Date, nullable=False)
    Store = db.Column(db.String(100), nullable=False)
    Region = db.Column(db.String(50), nullable=False)

    product = db.relationship('ExternalProduct', back_populates='sales_items')

    def __repr__(self):
        return f"<ExternalSalesDataItem Order={self.OrderId}, Product={self.ProductID}>"


class MarketingHistory(db.Model):
    """Track marketing content generation history"""
    __tablename__ = "marketing_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'csv', 'xlsx', 'image'
    content_type = db.Column(db.String(50), nullable=False)  # 'data', 'image'
    generated_content = db.Column(db.Text)  # JSON string of generated content
    status = db.Column(db.String(20), default='completed')  # 'completed', 'failed'
    error_message = db.Column(db.Text)
    rows_processed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship("User", backref=db.backref("marketing_history", lazy="dynamic", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<MarketingHistory {self.file_name} ({self.content_type})>"


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


# DB Setup
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()


@event.listens_for(User, "before_insert")
def default_user_approved(mapper, connection, target):
    if target.role == "shop_owner" and target.approved is None:
        target.approved = False
