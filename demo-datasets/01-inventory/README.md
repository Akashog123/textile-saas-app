# Inventory Upload Dataset

## File: `inventory_upload.csv`

This CSV file contains 20 sample textile products for inventory upload testing.

## Usage

1. Login as a **Shop Owner** or **Shop Manager**
2. Navigate to **Inventory** → **Import**
3. Upload `inventory_upload.csv`
4. Review and confirm the import

## Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| name | String | ✅ | Product display name |
| sku | String | ✅ | Unique stock keeping unit |
| category | String | ✅ | Product category (Cotton, Silk, etc.) |
| price | Number | ✅ | Unit price in INR |
| purchase_qty | Number | ✅ | Quantity to add to stock |
| minimum_stock | Number | ✅ | Reorder alert threshold |
| description | String | ❌ | Product description |
| distributor_id | Number | ❌ | Distributor reference ID |

## Sample Products Included

- Cotton Fabrics (3 varieties)
- Silk Fabrics (4 varieties)
- Linen, Wool, Brocade
- Georgette, Chiffon, Velvet
- Net, Rayon, Crepe
- Sustainable options (Khadi, Bamboo, Modal)

## API Endpoint

```
POST /api/inventory/shop/<shop_id>/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- file: inventory_upload.csv
```
