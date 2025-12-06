# Demo Datasets for SE-Textile-App

This directory contains sample datasets for testing all upload endpoints in the application.

## 📁 Directory Structure

```
demo-datasets/
├── README.md                          # This file
├── 01-inventory/                      # Inventory management uploads
│   └── inventory_upload.csv           # Products to add to shop inventory
├── 02-sales-data/                     # Sales tracking uploads
│   └── weekly_sales1.csv               # Weekly sales1 for shop owner 1 records
│   └── weekly_sales2.csv               # Weekly sales2 for shop owner 1 records
├── 03-marketing/                      
│   ├── marketing_products.csv
│   └── product_image.jpg
├── 04-distributor/
│   └── regional_sales.csv
└── 05-image-search/                   # Visual search sample images
    ├── sample_saree.jpg               # Saree for similarity search
    ├── sample_cotton_fabric.jpg       # Cotton fabric image
    └── sample_silk_fabric.jpg         # Silk fabric image
```

## 🔄 Upload Endpoints Reference

### 1. Inventory Upload (`/api/inventory/shop/<shop_id>/upload`)
- **File**: `01-inventory/inventory_upload.csv`
- **Method**: POST
- **Role**: shop_owner, shop_manager
- **Description**: Add multiple products to shop inventory

### 2. Sales Data Upload (`/api/shops/upload_sales_data`)
- **File**: `02-sales-data/weekly_sales1.csv`
- **Method**: POST
- **Role**: shop_owner, shop_manager
- **Description**: Upload weekly sales to update stock and enable AI insights

### 3. Marketing Content Generation (`/api/marketing/generate`)
- **Files**: 
  - `03-marketing/marketing_products.csv` (batch products)
  - `03-marketing/product_image.jpg` (single product image)
- **Method**: POST
- **Role**: shop_owner, shop_manager, distributor, manufacturer
- **Description**: Generate AI marketing captions and social media content

### 4. Production Planning (`/api/distributor/production-plan`)
- **File**: `04-distributor/regional_sales.csv`
- **Method**: POST
- **Role**: distributor, manufacturer
- **Description**: Upload regional sales data for AI production planning insights

### 5. Image Search (`/api/image-search/similar`)
- **Files**: `05-image-search/*.jpg`
- **Method**: POST
- **Role**: Any authenticated user
- **Description**: Find visually similar products by uploading an image

## 📋 Required Columns

### Inventory CSV
| Column | Required | Description |
|--------|----------|-------------|
| name | ✅ | Product name |
| sku | ✅ | Unique product identifier |
| category | ✅ | Product category |
| price | ✅ | Unit price in INR |
| purchase_qty | ✅ | Quantity to add |
| minimum_stock | ✅ | Reorder threshold |
| description | ❌ | Product description |

### Sales CSV
| Column | Required | Description |
|--------|----------|-------------|
| date | ✅ | Sale date (YYYY-MM-DD) |
| sku | ✅ | Product SKU |
| product_name | ✅ | Product name |
| category | ✅ | Product category |
| quantity_sold | ✅ | Units sold |
| selling_price | ✅ | Sale price |
| region | ❌ | Sales region |

### Marketing CSV
| Column | Required | Description |
|--------|----------|-------------|
| ProductName | ✅ | Product name |
| Category | ✅ | Product category |
| Price | ✅ | Product price |
| Description | ❌ | Product description |
| ImageURL | ✅ | Public image URL |

### Distributor/Production CSV
| Column | Required | Description |
|--------|----------|-------------|
| Date | ✅ | Sale date |
| Region | ✅ | Geographic region |
| Product | ✅ | Product name |
| Sales | ✅ | Sales amount/quantity |

## 🖼️ Image Files

All images in this demo dataset are actual product photos suitable for:
- Marketing content generation
- Visual similarity search
- Product catalog display

The images are stored locally and can be uploaded directly to test image-based features.

## 🚀 Quick Start

1. Login as a shop manager
2. Navigate to the relevant section (Inventory, Sales, Marketing, etc.)
3. Upload the corresponding CSV file from this directory
4. View the processed results

## ⚠️ Notes

- All dates in CSVs should be updated to current dates for realistic testing
- SKUs should be unique within your shop inventory
- Image URLs must be publicly accessible for marketing CSV uploads
- For image search, use JPG/PNG files under 16MB
