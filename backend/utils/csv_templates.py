# utils/csv_templates.py
"""
Centralized CSV Template Definitions for all import operations.
Each template defines required columns and provides downloadable headers.
"""

# ============================================================================
# INVENTORY IMPORT TEMPLATE
# ============================================================================
INVENTORY_COLUMNS = [
    "name",           # Product name (required)
    "sku",            # Stock Keeping Unit - unique identifier (required)
    "category",       # Product category e.g., Cotton, Silk, Linen (required)
    "price",          # Unit price in INR (required)
    "purchase_qty",   # Quantity being added to inventory (required)
    "minimum_stock",  # Safety stock level for reorder alerts (required)
    "description",    # Product description (optional)
    "distributor_id", # ID of the distributor/supplier (optional)
]

INVENTORY_REQUIRED = {"name", "sku", "category", "price", "purchase_qty", "minimum_stock"}

INVENTORY_SAMPLE_ROW = {
    "name": "Cotton Fabric Roll",
    "sku": "COT-001",
    "category": "Cotton",
    "price": "1500",
    "purchase_qty": "100",
    "minimum_stock": "20",
    "description": "Premium quality cotton fabric",
    "distributor_id": "",
}


# ============================================================================
# SALES DATA IMPORT TEMPLATE
# ============================================================================
SALES_COLUMNS = [
    "date",           # Sale date in YYYY-MM-DD format (required)
    "sku",            # Product SKU - must match inventory (required)
    "product_name",   # Product name for reference (required)
    "category",       # Product category (required)
    "quantity_sold",  # Number of units sold (required)
    "selling_price",  # Price per unit at sale (required)
    "region",         # Sales region/area (optional)
]

SALES_REQUIRED = {"date", "sku", "product_name", "category", "quantity_sold", "selling_price"}

SALES_SAMPLE_ROW = {
    "date": "2025-12-01",
    "sku": "COT-001",
    "product_name": "Cotton Fabric Roll",
    "category": "Cotton",
    "quantity_sold": "5",
    "selling_price": "1800",
    "region": "North",
}


# ============================================================================
# MARKETING CAMPAIGN TEMPLATE
# ============================================================================
MARKETING_COLUMNS = [
    "campaign_name",  # Name of the marketing campaign (required)
    "product_sku",    # Target product SKU (required)
    "start_date",     # Campaign start date YYYY-MM-DD (required)
    "end_date",       # Campaign end date YYYY-MM-DD (required)
    "budget",         # Campaign budget in INR (required)
    "channel",        # Marketing channel: social, email, print, etc. (required)
    "target_region",  # Target region for the campaign (optional)
    "description",    # Campaign description (optional)
]

MARKETING_REQUIRED = {"campaign_name", "product_sku", "start_date", "end_date", "budget", "channel"}

MARKETING_SAMPLE_ROW = {
    "campaign_name": "Summer Sale 2025",
    "product_sku": "COT-001",
    "start_date": "2025-06-01",
    "end_date": "2025-06-30",
    "budget": "50000",
    "channel": "social",
    "target_region": "All India",
    "description": "Summer discount campaign for cotton fabrics",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_template_csv(template_type: str, include_sample: bool = True) -> str:
    """
    Generate CSV content for a template.
    
    Args:
        template_type: One of 'inventory', 'sales', 'marketing'
        include_sample: Whether to include a sample data row
        
    Returns:
        CSV string with headers and optionally a sample row
    """
    templates = {
        "inventory": (INVENTORY_COLUMNS, INVENTORY_SAMPLE_ROW),
        "sales": (SALES_COLUMNS, SALES_SAMPLE_ROW),
        "marketing": (MARKETING_COLUMNS, MARKETING_SAMPLE_ROW),
    }
    
    if template_type not in templates:
        raise ValueError(f"Unknown template type: {template_type}. Available: {list(templates.keys())}")
    
    columns, sample = templates[template_type]
    
    # Header row
    csv_content = ",".join(columns) + "\n"
    
    # Sample row if requested
    if include_sample:
        sample_values = [str(sample.get(col, "")) for col in columns]
        csv_content += ",".join(sample_values) + "\n"
    
    return csv_content


def get_required_columns(template_type: str) -> set:
    """Get the set of required columns for a template type."""
    required_map = {
        "inventory": INVENTORY_REQUIRED,
        "sales": SALES_REQUIRED,
        "marketing": MARKETING_REQUIRED,
    }
    return required_map.get(template_type, set())


def get_all_columns(template_type: str) -> list:
    """Get all columns (required + optional) for a template type."""
    columns_map = {
        "inventory": INVENTORY_COLUMNS,
        "sales": SALES_COLUMNS,
        "marketing": MARKETING_COLUMNS,
    }
    return columns_map.get(template_type, [])


def validate_columns(df_columns: list, template_type: str) -> tuple:
    """
    Validate DataFrame columns against template requirements.
    
    Returns:
        (is_valid: bool, missing_columns: set, message: str)
    """
    required = get_required_columns(template_type)
    df_cols_lower = {c.lower().strip() for c in df_columns}
    
    missing = required - df_cols_lower
    
    if missing:
        return False, missing, f"Missing required columns: {', '.join(sorted(missing))}"
    
    return True, set(), "All required columns present"


# Template descriptions for API documentation
TEMPLATE_INFO = {
    "inventory": {
        "name": "Inventory Import Template",
        "description": "Use this template to add new products or restock existing inventory.",
        "required_columns": list(INVENTORY_REQUIRED),
        "all_columns": INVENTORY_COLUMNS,
        "notes": [
            "SKU must be unique per shop",
            "price is the purchase/cost price",
            "purchase_qty is the quantity being added",
            "minimum_stock triggers reorder alerts when inventory falls below this level"
        ]
    },
    "sales": {
        "name": "Sales Data Import Template", 
        "description": "Use this template to upload daily/weekly sales records for analytics.",
        "required_columns": list(SALES_REQUIRED),
        "all_columns": SALES_COLUMNS,
        "notes": [
            "SKU must match existing products in your inventory",
            "date format: YYYY-MM-DD (e.g., 2025-12-01)",
            "selling_price is the price at which the item was sold",
            "region is optional but helps with regional analytics"
        ]
    },
    "marketing": {
        "name": "Marketing Campaign Template",
        "description": "Use this template to plan and track marketing campaigns.",
        "required_columns": list(MARKETING_REQUIRED),
        "all_columns": MARKETING_COLUMNS,
        "notes": [
            "channel options: social, email, print, tv, radio, online",
            "budget is in INR",
            "product_sku should match your inventory"
        ]
    }
}
