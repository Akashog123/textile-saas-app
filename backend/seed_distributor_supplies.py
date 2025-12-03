"""Seed script for distributor_supplies table"""
from app import app
from models.model import db, DistributorSupply
from datetime import datetime, timedelta
import random

def seed_distributor_supplies():
    with app.app_context():
        # Clear existing data
        DistributorSupply.query.delete()
        db.session.commit()
        
        # Distributor IDs: 7 (distributor1), 8 (distributor2), 9 (manufacturer)
        distributors = [7, 8, 9]
        
        # Shop and Product mappings based on actual DB data
        shop_products = {
            1: list(range(1, 21)) + list(range(61, 71)),  # Shop 1: Products 1-20, 61-70
            2: list(range(21, 41)),                        # Shop 2: Products 21-40
            3: list(range(41, 61))                         # Shop 3: Products 41-60
        }
        
        # Product prices (from DB)
        product_prices = {
            1: 18356, 2: 14818, 3: 19221, 4: 16478, 5: 21383, 6: 16945, 7: 9041, 8: 23139, 9: 8396, 10: 17816,
            11: 19057, 12: 13977, 13: 15551, 14: 9316, 15: 18203, 16: 5247, 17: 17667, 18: 22603, 19: 13067, 20: 6388,
            21: 9917, 22: 23217, 23: 11331, 24: 9781, 25: 20446, 26: 9438, 27: 16815, 28: 24593, 29: 18560, 30: 17714,
            31: 18618, 32: 13051, 33: 24467, 34: 18810, 35: 6518, 36: 8967, 37: 22723, 38: 24198, 39: 16640, 40: 17515,
            41: 21970, 42: 7694, 43: 9895, 44: 24244, 45: 23879, 46: 9142, 47: 6217, 48: 8339, 49: 11103, 50: 9601,
            51: 21869, 52: 12811, 53: 24673, 54: 7471, 55: 10248, 56: 10125, 57: 7312, 58: 8456, 59: 21387, 60: 18932,
            61: 300, 62: 900, 63: 1300, 64: 800, 65: 600, 66: 450, 67: 400, 68: 1000, 69: 350, 70: 280
        }
        
        supplies = []
        base_date = datetime(2025, 6, 1)
        
        # Supply patterns - realistic distribution
        # Distributor 7 (distributor1) - primarily supplies to Shop 1 (Mumbai) and Shop 2 (Delhi)
        # Distributor 8 (distributor2) - primarily supplies to Shop 2 (Delhi) and Shop 3 (Jaipur)
        # Distributor 9 (manufacturer) - supplies to all shops
        
        supply_patterns = [
            # (distributor_id, shop_id, products_subset, num_supplies)
            (7, 1, shop_products[1][:15], 12),   # Dist 1 -> Shop 1 (Sarees)
            (7, 2, shop_products[2][:10], 8),    # Dist 1 -> Shop 2 (Sarees)
            (8, 2, shop_products[2][10:], 8),    # Dist 2 -> Shop 2 (Sarees)
            (8, 3, shop_products[3][:15], 10),   # Dist 2 -> Shop 3 (Sarees)
            (9, 1, shop_products[1][15:], 10),   # Manufacturer -> Shop 1 (Apparel + some sarees)
            (9, 2, shop_products[2][:8], 6),     # Manufacturer -> Shop 2
            (9, 3, shop_products[3][10:], 8),    # Manufacturer -> Shop 3
        ]
        
        notes_options = ["Regular order", "Bulk order", "Seasonal stock", "Festival demand"]
        
        record_id = 1
        for dist_id, shop_id, products, num_supplies in supply_patterns:
            for i in range(num_supplies):
                product_id = random.choice(products)
                quantity = random.randint(10, 100)
                # Distributor price is 70-85% of retail price
                unit_price = round(product_prices.get(product_id, 10000) * random.uniform(0.70, 0.85), 2)
                total_value = round(unit_price * quantity, 2)
                supply_date = base_date + timedelta(days=random.randint(0, 180))
                status = random.choice(['completed', 'completed', 'completed', 'pending'])
                note = f"Supply batch #{record_id} - {random.choice(notes_options)}"
                
                supply = DistributorSupply(
                    distributor_id=dist_id,
                    product_id=product_id,
                    shop_id=shop_id,
                    quantity_supplied=quantity,
                    unit_price=unit_price,
                    total_value=total_value,
                    supply_date=supply_date,
                    status=status,
                    notes=note
                )
                supplies.append(supply)
                record_id += 1
        
        db.session.add_all(supplies)
        db.session.commit()
        print(f"Created {len(supplies)} supply records successfully!")
        
        # Print summary
        print("\n=== SUPPLY SUMMARY ===")
        for dist_id in [7, 8, 9]:
            count = DistributorSupply.query.filter_by(distributor_id=dist_id).count()
            print(f"Distributor {dist_id}: {count} supplies")
        
        print("\n=== SAMPLE RECORDS ===")
        samples = DistributorSupply.query.limit(10).all()
        for s in samples:
            print(f"ID:{s.id} | Dist:{s.distributor_id} -> Shop:{s.shop_id} | Product:{s.product_id} | Qty:{s.quantity_supplied} | Rs.{s.total_value} | {s.status}")


if __name__ == "__main__":
    seed_distributor_supplies()
