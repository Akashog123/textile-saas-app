# Sales Data Upload Dataset

## File: `weekly_sales.csv`

This CSV contains 2 weeks of sample sales data (42 transactions) for testing sales analytics.

## Usage

1. Login as a **Shop Owner** or **Shop Manager**
2. Navigate to **Dashboard** → **Upload Sales Data**
3. Upload `weekly_sales.csv`
4. View updated AI insights and stock levels

## Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| date | Date | ✅ | Sale date (YYYY-MM-DD format) |
| sku | String | ✅ | Product SKU (must exist in inventory) |
| product_name | String | ✅ | Product name for reference |
| category | String | ✅ | Product category |
| quantity_sold | Number | ✅ | Units sold in this transaction |
| selling_price | Number | ✅ | Sale price per unit |
| region | String | ❌ | Sales region (North, South, East, West, Central) |

## Data Summary

- **Date Range**: Nov 18, 2025 - Dec 1, 2025
- **Total Transactions**: 42
- **Products**: 20 different SKUs
- **Regions**: 5 regions covered
- **Categories**: Cotton, Silk, Linen, Wool, Brocade, Georgette, Chiffon, Khadi, etc.

## What This Enables

After upload, the system will:
- Update inventory stock levels
- Generate AI-powered demand insights
- Create sales trends visualization
- Enable top-selling products analysis
- Provide regional performance metrics

## API Endpoint

```
POST /api/shops/upload_sales_data
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- file: weekly_sales.csv
```
