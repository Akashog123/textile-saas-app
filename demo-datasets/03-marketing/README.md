# Marketing Content Generation Dataset

## Files

### 1. `marketing_products.csv`
Batch product data with image URLs for generating multiple marketing captions at once.

### 2. `images/product_saree.jpg`
Single product image for individual marketing content generation.

## Usage

### Batch Upload (CSV)
1. Login as **Shop Owner**, **Shop Manager**, **Distributor**, or **Manufacturer**
2. Navigate to **Marketing** → **Generate Content**
3. Upload `marketing_products.csv`
4. Wait for AI to generate captions for all products
5. Download or copy generated content

### Single Image Upload
1. Navigate to **Marketing** → **Generate Content**
2. Upload `images/product_saree.jpg`
3. Optionally fill in product details (name, category, price)
4. Generate AI marketing content

## CSV Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| ProductName | String | ✅ | Product display name |
| Category | String | ✅ | Product category |
| Price | Number | ✅ | Product price in INR |
| Description | String | ❌ | Product description |
| ImageURL | String | ✅ | Public URL to product image |

## Products Included (10 items)

1. Royal Blue Silk Saree - ₹8,500
2. Designer Pink Banarasi Saree - ₹12,000
3. Cotton Printed Kurti - ₹1,200
4. Embroidered Anarkali Suit - ₹4,500
5. Raw Silk Fabric - ₹850/meter
6. Chanderi Cotton Dupatta - ₹1,800
7. Kalamkari Print Dress Material - ₹2,200
8. Men's Linen Kurta - ₹1,600
9. Bridal Lehenga Set - ₹35,000
10. Pashmina Shawl - ₹5,500

## Generated Content Types

The AI generates:
- **Social Media Captions** (Instagram, Facebook)
- **Product Descriptions** (E-commerce)
- **Promotional Headlines**
- **Hashtag Suggestions**

## API Endpoint

```
POST /api/marketing/generate
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- file: marketing_products.csv (for batch)
- file: product_image.jpg (for single image)
- product_name: "Product Name" (optional for image)
- product_category: "Category" (optional for image)
- product_price: "1000" (optional for image)
```
