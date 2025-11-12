import pandas as pd
from pathlib import Path

# Paths
BASE_PATH = Path(__file__).resolve().parent / "data" / "archive"

styles_path = BASE_PATH / "styles.csv"
output_path = BASE_PATH / "catalog.csv"

# Load data
df = pd.read_csv(styles_path, on_bad_lines='skip')

# Select relevant columns
df = df[[
    "id", "gender", "masterCategory", "subCategory",
    "articleType", "baseColour", "season", "year",
    "usage", "productDisplayName"
]]

# Rename columns for backend
df.rename(columns={
    "id": "product_id",
    "masterCategory": "category",
    "subCategory": "subcategory",
    "articleType": "article_type",
    "baseColour": "color",
    "productDisplayName": "product_name"
}, inplace=True)

# Add image URL paths
df["image_url"] = df["product_id"].apply(lambda x: f"/datasets/fashion-dataset/images/{x}.jpg")

# Save the processed catalog
df.to_csv(output_path, index=False)
print(f"✅ Catalog generated at: {output_path}")
print(f"Total products: {len(df)}")
