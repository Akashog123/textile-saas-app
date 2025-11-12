# import_tables.py

import os
import pandas as pd
from models.database import db
from models.models import Region, Product,SalesDataItem
from app import app
from datetime import datetime


# Path to your data file (update this if needed)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_REGION = os.path.join(BASE_DIR, '..', 'data', 'Textile-2', 'store_regions.csv')

  # or 'stores.csv'

def import_regions():
    # Read Excel or CSV file
    if DATA_FILE_REGION.endswith('.xlsx') or DATA_FILE_REGION.endswith('.xls'):
        df = pd.read_excel(DATA_FILE_REGION)
    elif DATA_FILE_REGION.endswith('.csv'):
        df = pd.read_csv(DATA_FILE_REGION)
    else:
        raise ValueError("Unsupported file format. Use .xlsx or .csv")

    with app.app_context():
        for _, row in df.iterrows():
            region = Region(
                StoreName=row['StoreName'],
                City=row['City'],
                Product_description=row['Product_description'],
                Latitude=row['Latitude'],
                Longitude=row['Longitude'],
                RegionName = row['RegionName'],
                ImagePath=row['ImagePath']
            )
            db.session.add(region)
        db.session.commit()
        print(f" Imported {len(df)} stores successfully!")

DATA_FILE_SALES = os.path.join(BASE_DIR, '..', 'data', 'Textile-2', 'sales_data.csv')
def import_sales_data():
    # Read Excel or CSV file
    if DATA_FILE_SALES.endswith('.xlsx') or DATA_FILE_SALES.endswith('.xls'):
        df = pd.read_excel(DATA_FILE_SALES)
    elif DATA_FILE_SALES.endswith('.csv'):
        df = pd.read_csv(DATA_FILE_SALES)
    else:
        raise ValueError("Unsupported file format. Use .xlsx or .csv")

    # Ensure correct column names
    expected_cols = ['Productid', 'OrderId', 'UnitsSold', 'Sales', 'SaleDate', 'Store', 'Region']
    for col in expected_cols:
        if col not in df.columns:
            raise KeyError(f"Missing column: {col}")

    with app.app_context():
        for _, row in df.iterrows():
            try:
                # Convert SaleDate string to date
                sale_date = pd.to_datetime(row['SaleDate'], errors='coerce').date()

                sale_item = SalesDataItem(
                    ProductID=row['Productid'],
                    OrderId=row['OrderId'],
                    UnitsSold=row['UnitsSold'],
                    Sales=row['Sales'],
                    SaleDate=sale_date,
                    Store=row['Store'],
                    Region=row['Region']
                )

                db.session.add(sale_item)
            except Exception as e:
                print(f" Skipped row due to error: {e}")

        db.session.commit()
        print(f" Imported {len(df)} sales records successfully!")
DATA_FILE = os.path.join(BASE_DIR, '..', 'data', 'Textile-2', 'products.csv')  # or .xlsx

def import_products():
    # ✅ Read the file (supports CSV or Excel)
    if DATA_FILE.endswith('.xlsx') or DATA_FILE.endswith('.xls'):
        df = pd.read_excel(DATA_FILE)
    elif DATA_FILE.endswith('.csv'):
        df = pd.read_csv(DATA_FILE)
    else:
        raise ValueError("Unsupported file format. Use .xlsx or .csv")

    print(f"📦 Importing {len(df)} products from {DATA_FILE}")

    with app.app_context():
        for _, row in df.iterrows():
            try:
                product = Product(
                    ProductID=row['Productid'],
                    ProductCategory=row['ProductCategory'],
                    Occasion=row.get('Occasion', None),
                    Material=row.get('Material', None),
                    Karigari=row.get('Karigari', None),
                    Karigari_description=row.get('Karigari_description', None),
                    Product_description=row.get('Product_description', None)
                )
                db.session.add(product)
            except Exception as e:
                print(f"⚠️ Skipped row due to error: {e}")

        db.session.commit()
        print(f"✅ Successfully imported {len(df)} products!")

if __name__ == "__main__":
    import_regions()
    import_sales_data()
    import_products()
