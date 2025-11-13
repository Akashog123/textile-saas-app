#app.py file

from flask import Flask, jsonify,request
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import google.generativeai as genai
from PIL import Image
import io
import tempfile
from collections import OrderedDict
# Import models and database instance
from models.database import db
from models.models import Region,Product,SalesDataItem

from flask import Response
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
# Initialize Flask app
app = Flask(__name__)

genai.configure(api_key="AIzaSyB4124DMFesEd6NXYhzsk6BQBIuKgZmnog")
#model = genai.GenerativeModel("gemini-2.5-flash")
#  Configure database (SQLite by default)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#  Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

#  Simple route for health check

genai_model = None
def get_model():
    global genai_model
    if genai_model is None:
        genai_model = genai.GenerativeModel("gemini-2.5-flash")
    return genai_model


@app.route('/')
def home():
    return jsonify({"message": " Textile Flask API is running!"})

#  Route to view all stores
@app.route('/stores', methods=['GET'])
def get_stores():
    stores = Region.query.order_by(Region.RegionID.asc()).all()
    
    store_list = [
        OrderedDict([
            ("id", s.RegionID),
            ("name", s.StoreName),
            ("Latitude", s.Latitude),
            ("Longitude", s.Longitude),
            ("Region",s.RegionName),
            ("ImagePath", s.ImagePath)
        ])
        for s in stores
    ]
    return Response(
        json.dumps(store_list, sort_keys=False),
        mimetype='application/json'
    )
def extract_image_features(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((48, 48))  # small for faster comparison
    return np.array(img).flatten()

#  Directory with comparison images
STORE_IMAGES_DIR = os.path.join(os.getcwd(), "data", "store_images")
print(os.getcwd())
@app.route('/compare-images', methods=['POST'])
def compare_images():
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity
    #  Expect one input image
    if 'input_image' not in request.files:
        return jsonify({"error": "Send 'input_image' file"}), 400

    input_image = request.files['input_image'].read()
    input_features = extract_image_features(input_image)

    #  Load all images from folder
    image_files = [
        f for f in os.listdir(STORE_IMAGES_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
    ]
    print(image_files)
    if not image_files:
        return jsonify({"error": "No images found in store_images folder"}), 404

    comparison_features = []
    valid_files = []

    for filename in image_files:
        try:
            with open(os.path.join(STORE_IMAGES_DIR, filename), "rb") as img_file:
                features = extract_image_features(img_file.read())
                comparison_features.append(features)
                relative_path = os.path.join("data", "store_images", filename)
                valid_files.append(relative_path)
        except Exception as e:
            print(f" Skipped {filename}: {e}")

    #  Standardize + Compare
    scaler = StandardScaler()
    all_scaled = scaler.fit_transform([input_features] + comparison_features)
    similarities = cosine_similarity([all_scaled[0]], all_scaled[1:])[0]

    best_match_index = int(np.argmax(similarities))
    best_match_file = valid_files[best_match_index]

    return jsonify({
        "best_match_file": best_match_file,
        "similarity_score": float(similarities[best_match_index])
    })
# ============================
#  AI-Powered Top-Selling Report
# ============================



@app.route('/top-selling-products', methods=['GET'])
def top_selling_products():

    
    """
    As a manufacturer, this endpoint uses AI to generate
    top-selling product reports by region and month to plan next month's production.
    """

    # Step 1: Fetch only first 5 ProductIDs
    top_5_product_ids = [p.ProductID for p in Product.query.order_by(Product.ProductID).limit(5).all()]

    if not top_5_product_ids:
        return jsonify({"error": "No products found in database"}), 404

    # Step 2: Fetch joined data only for these products
    sales_data = (
        db.session.query(
            SalesDataItem.ProductID,
            SalesDataItem.Region,
            SalesDataItem.SaleDate,
            SalesDataItem.UnitsSold,
            SalesDataItem.Sales,
            Product.ProductCategory.label('ProductName')
        )
        .join(Product, SalesDataItem.ProductID == Product.ProductID)
        .filter(SalesDataItem.ProductID.in_(top_5_product_ids))
        .all()
    )

    if not sales_data:
        return jsonify({"error": "No sales data available for selected products"}), 404

    # Step 3: Convert to DataFrame
    df = pd.DataFrame([{
        "ProductID": s.ProductID,
        "Region": s.Region,
        "ProductName": s.ProductName,
        "UnitsSold": s.UnitsSold,
        "Revenue": s.Sales,
        "Date": s.SaleDate
    } for s in sales_data])

    # Step 4: Preprocess and Aggregate
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.strftime('%B %Y')

    summary_df = (
        df.groupby(['ProductID', 'Region', 'Month', 'ProductName'])
        .agg({'UnitsSold': 'sum', 'Revenue': 'sum'})
        .reset_index()
    )

    # Step 5: Prepare summary text for AI
    summary_text = summary_df.to_string(index=False)

    # Step 6: Ask Gemini AI for insights
    prompt = f"""
    You are an AI business analyst for a textile manufacturer.
    Based on the below summarized sales data (ProductID, Region, Month, ProductName, UnitsSold, Revenue),
    identify the top-selling products by region and month,
    and provide clear, concise recommendations for next month's production planning.

    Summarized Sales Data:
    {summary_text}

    Output format:
    - ProductID
    - Region
    - Month
    - Top 3 Products (with UnitsSold and Revenue)
    - AI Recommendation (1-2 sentences).
    """

    try:
        model = get_model()
        ai_response = model.generate_content(prompt)
        ai_text = ai_response.text.strip() if hasattr(ai_response, "text") else str(ai_response)

        return jsonify({
            "status": "success",
            "summary_table": summary_df.to_dict(orient="records"),
            "ai_analysis": ai_text
        })

    except Exception as e:
        return jsonify({
            "error": f"AI processing failed: {str(e)}"
        }), 500



@app.route('/ai-find-stores', methods=['POST'])
def ai_find_stores():
    """
    AI-enabled endpoint:
    - Input: either JSON text prompt or uploaded voice file
    - Output: matching rows from Region table as JSON
    """

    user_prompt = None
    audio_file = None
    data = request.form if request.form else request.get_json(silent=True)
    user_prompt = data.get("prompt") if data else None
    audio_file = request.files.get("voice_note")

    # Validate input
    if not user_prompt and not audio_file:
        return jsonify({
            "error": "Either 'prompt' (text) or 'voice_note' (audio file) is required."
        }), 400

    # Step 1️⃣ — If voice input, transcribe using Gemini
    if audio_file:
        try:
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                audio_path = tmp.name
                audio_file.save(audio_path)

            model = get_model()
            # Gemini automatically understands audio content for transcription
            transcription_prompt = "Transcribe this audio into text for a store search query."
            ai_response = model.generate_content([transcription_prompt, {"mime_type": "audio/wav", "data": open(audio_path, "rb").read()}])
            user_prompt = ai_response.text.strip()
        except Exception as e:
            return jsonify({"error": f"Voice transcription failed: {e}"}), 500

    # Step 2️⃣ — Fetch all store data
    stores = Region.query.all()
    if not stores:
        return jsonify({"error": "No stores found in database"}), 404

    store_data = [
        {
            "StoreName": s.StoreName,
            "City": s.City,
            "Product_description": s.Product_description,
            "Latitude": s.Latitude,
            "Longitude": s.Longitude,
            "RegionName": s.RegionName,
            "ImagePath": s.ImagePath
        }
        for s in stores
    ]

    # Step 3️⃣ — Build AI prompt for semantic matching
    search_prompt = f"""
    You are a textile shop finder assistant.
    The customer says: "{user_prompt}"

    The available stores are:
    {store_data}

    Identify which stores best match the customer's query
    based on the Product_description field.
    Return ONLY a JSON array of matching stores with these keys:
    ["StoreName", "City", "Product_description", "Latitude", "Longitude", "RegionName", "ImagePath"]
    """

    try:
        model = get_model()
        ai_response = model.generate_content(search_prompt)
        ai_text = ai_response.text.strip()
    except Exception as e:
        return jsonify({"error": f"AI search failed: {e}"}), 500

    # Step 4️⃣ — Extract clean JSON from Gemini response
    import re, json
    try:
        match = re.search(r'\[.*\]', ai_text, re.DOTALL)
        ai_json = json.loads(match.group(0)) if match else []
    except Exception:
        ai_json = []

    # Step 5️⃣ — Return results
    return jsonify({
        "matches_found": len(ai_json),
        "matching_stores": ai_json
    })


@app.route('/trending-shops', methods=['GET'])
def trending_shops():
    """
    As a customer, I want to review shops and see trending patterns
    so I can make informed purchase decisions.
    Combines Region and SalesDataItem data to analyze shop trends.
    """

    try:
        # Step 1️⃣ — Fetch joined data
        recent_sales = (
            db.session.query(
                SalesDataItem.Store,
                SalesDataItem.Region,
                SalesDataItem.SaleDate,
                SalesDataItem.UnitsSold,
                SalesDataItem.Sales,
                Region.StoreName,
                Region.City,
                Region.RegionName
            )
            .join(Region, SalesDataItem.Store == Region.StoreName)
            .all()
        )

        if not recent_sales:
            return jsonify({"error": "No sales or store data found."}), 404

        # Step 2️⃣ — Convert to DataFrame
        df = pd.DataFrame([{
            "Store": s.Store,
            "Region": s.Region,
            "SaleDate": s.SaleDate,
            "UnitsSold": s.UnitsSold,
            "Sales": s.Sales,
            "City": s.City,
            "RegionName": s.RegionName
        } for s in recent_sales])

        # Step 3️⃣ — Clean and group
        df["SaleDate"] = pd.to_datetime(df["SaleDate"], errors='coerce')
        df["Month"] = df["SaleDate"].dt.strftime("%B %Y")

        # Aggregate sales by month & store
        trend_df = (
            df.groupby(["Store", "City", "RegionName", "Month"])
            .agg({"UnitsSold": "sum", "Sales": "sum"})
            .reset_index()
            .sort_values(["RegionName", "Month", "Sales"], ascending=[True, True, False])
        )

        # Step 4️⃣ — Prepare text summary for AI
        table_text = trend_df.head(50).to_string(index=False)
        ai_prompt = f"""
        You are an AI textile retail analyst.
        Analyze the below monthly sales data of different stores and regions.
        Identify:
        1. Which shops are trending (rising sales or strong performance)
        2. Which regions have high demand
        3. What kinds of products might be driving the trend (infer from context if possible)
        4. Give recommendations for customers looking for popular shops.

        Monthly Sales Data:
        {table_text}

        Respond in JSON format:
        {{
          "top_trending_shops": [
             {{
               "StoreName": "...",
               "RegionName": "...",
               "Trend": "Upward/Stable/Downward",
               "AI_Comment": "..."
             }}
          ],
          "customer_recommendation": "..."
        }}
        """

        # Step 5️⃣ — Use Gemini AI for summarization
        model = get_model()
        ai_response = model.generate_content(ai_prompt)
        ai_text = ai_response.text.strip()

        # Step 6️⃣ — Extract JSON cleanly
        import re, json
        try:
            match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            ai_json = json.loads(match.group(0)) if match else {}
        except Exception:
            ai_json = {"error": "AI output parsing failed", "raw_output": ai_text}

        return jsonify({
            "status": "success",
            "trend_data": trend_df.to_dict(orient="records"),
            "ai_analysis": ai_json
        })

    except Exception as e:
        return jsonify({"error": f"Trending analysis failed: {str(e)}"}), 500

#  Run app
if __name__ == '__main__':
    db_path = os.path.join(app.instance_path, "data.db")
    if not os.path.exists(db_path):
        print("Database not found — creating new one...")
        db.create_all()
    else:
        print("Database already exists, skipping creation.")
    
    
    app.run(debug=True)
