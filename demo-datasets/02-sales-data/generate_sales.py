import csv
import random
from datetime import datetime, timedelta

# Paths
inventory_path = r'd:\Projects\SE-Textile-App\demo-datasets\01-inventory\inventory_upload1.csv'
sales1_path = r'd:\Projects\SE-Textile-App\demo-datasets\02-sales-data\weekly_sales1.csv'
sales2_path = r'd:\Projects\SE-Textile-App\demo-datasets\02-sales-data\weekly_sales2.csv'

# Read inventory
products = []
# Read inventory
products = []
with open(inventory_path, 'r', newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    # clean fieldnames if necessary (though DictReader reads them from first line)
    reader.fieldnames = [name.strip() for name in reader.fieldnames]
    
    for row in reader:
        # inventory cols: name,sku,category,price,purchase_qty,minimum_stock,description,distributor_username
        # Handle potential whitespace in keys from the row dict itself if manually constructed, 
        # but here the reader uses fieldnames we just stripped.
        
        products.append({
            'sku': row['sku'],
            'product_name': row['name'],
            'category': row['category'],
            'cost_price': float(row['price'])
        })

regions = ['North', 'South', 'East', 'West', 'Central']

def generate_sales(start_date, days, products, regions):
    sales_data = []
    # Generate 3-5 sales per day for random products
    current_date = start_date
    for _ in range(days):
        date_str = current_date.strftime('%Y-%m-%d')
        # Random number of transactions per day
        num_transactions = random.randint(3, 8) 
        
        daily_products = random.sample(products, min(len(products), num_transactions))
        
        for prod in daily_products:
            # Random markup 10% to 30%
            markup = random.uniform(1.1, 1.3)
            selling_price = round(prod['cost_price'] * markup / 50) * 50 # Round to nearest 50
            
            qty = random.randint(1, 20)
            
            sale = {
                'date': date_str,
                'sku': prod['sku'],
                'product_name': prod['product_name'],
                'category': prod['category'],
                'quantity_sold': qty,
                'selling_price': int(selling_price),
                'region': random.choice(regions)
            }
            sales_data.append(sale)
        
        current_date += timedelta(days=1)
    
    return sales_data

def write_sales(path, data):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'sku', 'product_name', 'category', 'quantity_sold', 'selling_price', 'region']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Week 1: Nov 18 to Nov 24
start_date1 = datetime(2025, 11, 18)
sales1 = generate_sales(start_date1, 7, products, regions)
write_sales(sales1_path, sales1)

# Week 2: Nov 29 to Dec 12
start_date2 = datetime(2025, 11, 29)
sales2 = generate_sales(start_date2, 14, products, regions)
write_sales(sales2_path, sales2)

print(f"Generated {len(sales1)} records for Week 1 at {sales1_path}")
print(f"Generated {len(sales2)} records for Week 2 at {sales2_path}")
