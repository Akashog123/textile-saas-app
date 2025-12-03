# Distributor Production Planning Dataset

## File: `regional_sales.csv`

Regional sales data for AI-powered production planning and demand forecasting.

## Usage

1. Login as a **Distributor** or **Manufacturer**
2. Navigate to **Production Planning**
3. Upload `regional_sales.csv`
4. View AI-generated production recommendations and forecasts

## Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| Date | Date | ✅ | Sales date (YYYY-MM-DD) |
| Region | String | ✅ | Geographic region |
| Product | String | ✅ | Product category/type |
| Sales | Number | ✅ | Sales amount in INR |

## Data Summary

- **Date Range**: Sep 1, 2025 - Nov 24, 2025 (12 weeks)
- **Regions**: North, South, East, West, Central
- **Products**: Silk, Cotton, Linen, Wool, Brocade
- **Total Records**: 65 weekly entries

## Sales Trends in Data

| Product | Trend | Peak Region |
|---------|-------|-------------|
| Silk | 📈 Strong growth (125K → 285K) | North |
| Cotton | 📊 Stable with slight growth | South |
| Linen | 📉 Declining | East |
| Wool | 📈 Seasonal increase (winter) | West |
| Brocade | 📈 Festive season growth | Central |

## AI Insights Generated

After upload, the system provides:

1. **Forecasted Demand** - 30-day Prophet forecast
2. **Production Priorities** - Increase, Maintain, Reduce recommendations
3. **Regional Analysis** - Best performing regions per product
4. **Seasonal Adjustments** - Textile-specific seasonality

## API Endpoint

```
POST /api/distributor/production-plan
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- file: regional_sales.csv
```

## Sample Format Endpoint

Get the expected CSV structure:
```
GET /api/distributor/sample-format
```
