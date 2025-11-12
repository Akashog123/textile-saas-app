#models.py file

from models.database import db

class Region(db.Model):
    __tablename__ = 'region'

    RegionID = db.Column(db.Integer, primary_key=True)
    StoreName = db.Column(db.String(100), nullable=False)
    City = db.Column(db.String(100), nullable=False)
    Product_description = db.Column(db.String(500), nullable=False)
    Latitude = db.Column(db.Float, nullable=False)
    Longitude = db.Column(db.Float, nullable=False)
    RegionName=db.Column(db.String(50), nullable=False)
    ImagePath = db.Column(db.String(255), nullable=True)

    def __init__(self, StoreName,City,Product_description, Latitude, Longitude,RegionName, ImagePath):
        self.StoreName = StoreName
        self.City = City
        self.Product_description = Product_description
        self.Latitude = Latitude
        self.Longitude = Longitude
        self.RegionName = RegionName
        self.ImagePath = ImagePath

    def __repr__(self):
        return f"<Store {self.StoreName}>"
from models.database import db

class Product(db.Model):
    __tablename__ = 'product'

    ID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, unique=True, nullable=False)
    ProductCategory = db.Column(db.String(100), nullable=False)
    Occasion = db.Column(db.String(100), nullable=True)
    Material = db.Column(db.String(100), nullable=True)
    Karigari = db.Column(db.String(100), nullable=True)
    Karigari_description = db.Column(db.Text, nullable=True)
    Product_description = db.Column(db.Text, nullable=True)

    # One-to-many relationship with SalesDataItem
    sales_items = db.relationship('SalesDataItem', back_populates='product', cascade='all, delete-orphan')

    def __init__(self, ProductID,ProductCategory, Occasion, Material, Karigari, Karigari_description, Product_description):
        self.ProductID = ProductID
        self.ProductCategory = ProductCategory
        self.Occasion = Occasion
        self.Material = Material
        self.Karigari = Karigari
        self.Karigari_description = Karigari_description
        self.Product_description = Product_description

    def __repr__(self):
        return f"<Product {self.ProductID} - {self.ProductCategory}>"


class SalesDataItem(db.Model):
    __tablename__ = 'sales_data_item'

    id = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey('product.ProductID'), nullable=False)
    OrderId = db.Column(db.Integer, nullable=False)
    UnitsSold = db.Column(db.Integer, nullable=False)
    Sales = db.Column(db.Float, nullable=False)
    SaleDate = db.Column(db.Date, nullable=False)
    Store = db.Column(db.String(100), nullable=False)
    Region = db.Column(db.String(50), nullable=False)

    # Relationship to Product
    product = db.relationship('Product', back_populates='sales_items')

    def __init__(self, ProductID, OrderId, UnitsSold, Sales, SaleDate, Store, Region):
        self.ProductID = ProductID
        self.OrderId = OrderId
        self.UnitsSold = UnitsSold
        self.Sales = Sales
        self.SaleDate = SaleDate
        self.Store = Store
        self.Region = Region

    def __repr__(self):
        return f"<SalesDataItem {self.OrderId} - Product {self.ProductID}>"
