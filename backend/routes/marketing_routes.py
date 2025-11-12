import os
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.ai_service import generate_ai_caption, forecast_trends, generate_marketing_poster

# ───────────────────────────────────────────────
# Blueprint Setup
# ───────────────────────────────────────────────
marketing_bp = Blueprint("marketing", __name__)

UPLOAD_FOLDER = "./uploads/marketing"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg"}


# ───────────────────────────────────────────────
# Helper: File Validation
# ───────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ───────────────────────────────────────────────
# 📤 POST: Upload CSV/Image → Generate AI Marketing Insights + Poster
# ───────────────────────────────────────────────
@marketing_bp.route("/generate", methods=["POST"])
def generate_marketing_content():
    """
    Handles product uploads (CSV/XLSX/Image) and uses AI to generate:
    - Product captions (via Gemini)
    - Sales trends (if applicable)
    - AI-generated marketing poster (for image uploads)
    """
    try:
        # Retrieve uploaded file
        file = request.files.get("file")
        if not file or not allowed_file(file.filename):
            return jsonify({
                "status": "error",
                "message": "Invalid or missing file. Please upload a CSV, XLSX, or image file."
            }), 400

        # Save file securely
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        result = {"filename": filename}
        ai_captions, trend_data = [], []

        # ──────────────── CASE 1: CSV / XLSX Upload ────────────────
        if filename.endswith((".csv", ".xlsx")):
            df = pd.read_csv(filepath) if filename.endswith(".csv") else pd.read_excel(filepath)

            # Required columns for marketing caption generation
            required_cols = {"ProductName", "Category", "Price"}
            if not required_cols.issubset(df.columns):
                return jsonify({
                    "status": "error",
                    "message": "Missing columns. File must contain: ProductName, Category, and Price."
                }), 400

            # Generate captions using AI for top 5 products
            for _, row in df.head(5).iterrows():
                product = row.get("ProductName", "Fabric")
                category = row.get("Category", "Textile")
                price = row.get("Price", 1000)
                caption = generate_ai_caption(product, category, price)

                ai_captions.append({
                    "product": product,
                    "category": category,
                    "caption": caption
                })

            # Generate sales trend forecast (if applicable)
            if {"Date", "Sales"}.issubset(df.columns):
                trend_data = forecast_trends(df)

            result.update({
                "type": "data",
                "ai_captions": ai_captions,
                "forecast": trend_data,
                "rows_processed": len(df),
                "analyst": "Guest User"
            })

        # ──────────────── CASE 2: Image Upload ────────────────
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            # Step 1: AI Caption from Image
            caption = generate_ai_caption(
                f"Uploaded product image: {filename}",
                "Fabric/Clothing",
                1200,
                image_path=filepath
            )

            # Step 2: Generate AI Poster + Prompt
            poster_prompt, poster_path = generate_marketing_poster(filepath)

            result.update({
                "type": "image",
                "caption": caption,
                "poster_prompt": poster_prompt or "AI prompt not available.",
                "poster": f"/uploads/marketing/{os.path.basename(poster_path)}" if poster_path else None,
                "preview": f"/uploads/marketing/{filename}",
                "analyst": "Guest User"
            })

        # ──────────────── SUCCESS RESPONSE ────────────────
        print(f"✅ [Marketing AI] Processed file: {filename}")
        return jsonify({
            "status": "success",
            "message": "AI marketing content generated successfully!",
            "result": result
        }), 200

    except Exception as e:
        print("❌ [Marketing AI Error]:", e)
        return jsonify({
            "status": "error",
            "message": "Failed to process marketing content.",
            "error": str(e)
        }), 500


# ───────────────────────────────────────────────
# 📜 GET: Allowed File Extensions
# ───────────────────────────────────────────────
@marketing_bp.route("/allowed-extensions", methods=["GET"])
def get_allowed_extensions():
    """Return allowed file types for upload."""
    return jsonify({
        "status": "success",
        "allowed_extensions": sorted(list(ALLOWED_EXTENSIONS))
    }), 200
