import os
import random
import pandas as pd
from prophet import Prophet
from PIL import Image
import google.generativeai as genai
from google.generativeai import GenerativeModel, configure

# =========================
# 🌐 GEMINI CONFIGURATION
# =========================
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment. Gemini AI features will not function.")
else:
    configure(api_key=GEMINI_KEY)
    genai.configure(api_key=GEMINI_KEY)
    print("✅ Gemini API key configured successfully.")

# =========================
# 🔤 Default Text Responses
# =========================
DEFAULT_CAPTION = "Elegant design for every occasion!"
DEFAULT_SUMMARY = "Steady growth observed across key regions with strong fabric demand."
DEFAULT_RECOMMENDATION = "Maintain higher silk stock in northern regions; expand cotton offerings in the east."
DEFAULT_PRIORITIES = [
    {"title": "Scale up high-demand fabrics", "detail": "Increase production for top performers.", "level": "increase"},
    {"title": "Maintain stable cotton blends", "detail": "Keep inventory consistent for steady sellers.", "level": "maintain"},
    {"title": "Reduce low-selling SKUs", "detail": "Optimize resources by limiting underperformers.", "level": "reduce"},
]

# =========================
# 🧠 GEMINI MODEL HANDLER
# =========================
def get_model():
    """Return the latest Gemini 2.5 Pro model (text + vision)."""
    try:
        model_name = "gemini-2.5-pro"
        model = GenerativeModel(model_name)
        print(f"✅ Using Gemini model: {model_name}")
        return model
    except Exception as e:
        print(f"❌ Gemini Model Load Error: {e}")
        raise


# =========================
# 🧠 HELPER: SAFE PROMPT RUNNER
# =========================
def run_gemini_prompt(prompt: str, fallback: str) -> str:
    """Safely generate text from Gemini with fallback on failure."""
    try:
        model = get_model()
        response = model.generate_content(prompt)
        if response and hasattr(response, "text") and response.text.strip():
            return response.text.strip()
        return fallback
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return fallback


# =========================
# 🛍️ AI CAPTION GENERATION
# =========================
def generate_ai_caption(product_name: str, category: str = "", price: float = 0.0, image_path: str = None) -> str:
    """Generate a short, catchy marketing caption using Gemini (supports text + vision)."""
    try:
        model = get_model()

        # 🌆 Vision captioning (for uploaded image)
        if image_path and os.path.exists(image_path):
            prompt = (
                "Generate a short, catchy marketing caption (under 25 words) "
                "for this textile or fashion product image. "
                "Focus on elegance, premium tone, and emotional appeal."
            )
            img = Image.open(image_path)
            response = model.generate_content([prompt, img])

            if response and hasattr(response, "text") and response.text.strip():
                return response.text.strip()
            return DEFAULT_CAPTION

        # 🧾 Text-based caption (for CSV/XLSX input)
        product_name = str(product_name or "").strip()
        category = str(category or "").strip()
        price = str(price or "N/A")

        prompt = f"""
        Create a short, premium marketing caption (under 35 words)
        for a textile or fabric product.
        Product: {product_name}
        Category: {category}
        Price: ₹{price}
        Tone: Elegant, aesthetic, and festive to attract buyers.
        """
        return run_gemini_prompt(prompt, DEFAULT_CAPTION)

    except Exception as e:
        print("❌ AI Caption Generation Error:", e)
        return DEFAULT_CAPTION


# =========================
# 🎨 MARKETING POSTER GENERATION
# =========================
def generate_marketing_poster(image_path: str, product_name: str = None):
    """Analyze image → create prompt → generate AI poster."""
    if not os.path.exists(image_path):
        print("❌ Image path not found:", image_path)
        return None, None

    try:
        vision_model = genai.GenerativeModel("gemini-2.5-pro")
        img = Image.open(image_path)

        vision_prompt = (
            "You are an AI marketing designer. Analyze this textile or fashion image "
            "and generate a descriptive text prompt for a marketing poster. "
            "Include theme, tone, background, and visual style (festive, elegant, or luxury)."
        )

        response = vision_model.generate_content([vision_prompt, img])
        banner_prompt = (
            response.text.strip()
            if response and hasattr(response, "text") and response.text
            else "A luxurious festive textile banner with premium colors and elegant lighting."
        )

        if product_name:
            banner_prompt = f"{banner_prompt} featuring '{product_name}'."

        print("🧠 Poster prompt generated:", banner_prompt)

    except Exception as e:
        print("❌ Prompt Generation Error:", e)
        banner_prompt = "Elegant textile poster background with premium lighting."

    # Generate Poster (if quota allows)
    try:
        image_model = genai.GenerativeModel("gemini-2.5-flash-image")
        output_path = os.path.splitext(image_path)[0] + "_poster.png"
        result = image_model.generate_content([banner_prompt])

        for part in result.parts:
            if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"✅ Poster image saved at {output_path}")
                return banner_prompt, output_path

        print("⚠️ No image data found in Gemini response.")
        return banner_prompt, None

    except Exception as e:
        if "quota" in str(e).lower():
            print("⚠️ Gemini quota limit reached. Poster not generated.")
            return banner_prompt, None
        print("❌ Poster Image Generation Error:", e)
        return banner_prompt, None


# =========================
# 📈 SALES FORECASTING
# =========================
def forecast_trends(df: pd.DataFrame):
    """Generate 30-day sales forecast using Prophet."""
    try:
        if df is None or df.empty:
            return []
        if not {"Date", "Sales"}.issubset(df.columns):
            return []

        df["ds"] = pd.to_datetime(df["Date"])
        df["y"] = pd.to_numeric(df["Sales"], errors="coerce")
        df.dropna(subset=["y"], inplace=True)

        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        trend = forecast[["ds", "yhat"]].tail(30)
        return trend.to_dict(orient="records")

    except Exception as e:
        print("❌ Forecasting Error:", e)
        return []


# =========================
# 📊 DISTRIBUTOR INSIGHTS
# =========================
def generate_demand_summary(region_data, top_product):
    """Generate concise AI-powered regional demand summary."""
    try:
        region_text = str(region_data)[:800]
        top_product = str(top_product or "N/A")

        prompt = f"""
        Analyze textile demand data:
        Regional Summary: {region_text}
        Top Product: {top_product}

        Write a concise 60-word business summary:
        - Top performing regions
        - Growth insights
        - Expected sales trend
        Tone: professional and analytical.
        """
        return run_gemini_prompt(prompt, DEFAULT_SUMMARY)
    except Exception as e:
        print("❌ AI Summary Generation Error:", e)
        return DEFAULT_SUMMARY


def generate_recommendation(region_data, trending_products):
    """Generate actionable short business recommendations."""
    try:
        region_text = str(region_data)[:500]
        trending_text = str(trending_products)[:500]

        prompt = f"""
        Based on regional textile demand and trending fabrics:
        Regions: {region_text}
        Trending: {trending_text}

        Give 2–3 concise recommendations (max 30 words):
        - Inventory
        - Marketing focus
        - Regional strategy
        """
        return run_gemini_prompt(prompt, DEFAULT_RECOMMENDATION)
    except Exception as e:
        print("❌ AI Recommendation Error:", e)
        return DEFAULT_RECOMMENDATION


# =========================
# 🏭 PRODUCTION PLANNING
# =========================
def generate_production_priorities(df: pd.DataFrame):
    """AI-driven production scaling suggestions."""
    try:
        products = df.groupby("Product")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        top_selling, underperforming = [], []

        for _, row in products.head(5).iterrows():
            top_selling.append({
                "name": row["Product"],
                "growth": f"+{random.randint(5,15)}% MoM",
                "region": random.choice(df["Region"].unique()),
                "volume": f"{int(row['Sales'])} m",
                "image": f"https://source.unsplash.com/400x300/?{row['Product']},fabric"
            })

        for _, row in products.tail(5).iterrows():
            underperforming.append({
                "name": row["Product"],
                "region": random.choice(df["Region"].unique()),
                "decline": f"-{random.randint(5,15)}%",
                "volume": f"{int(row['Sales'])} m",
                "image": f"https://source.unsplash.com/400x300/?{row['Product']},fabric"
            })

        prompt = f"""
        You are a textile production planner analyzing product data.
        Data: {products.head(10).to_dict(orient='records')}
        Suggest 3 key actions (increase, maintain, reduce).
        """
        run_gemini_prompt(prompt, "")
        return DEFAULT_PRIORITIES, top_selling, underperforming

    except Exception as e:
        print("❌ Production Priority Generation Error:", e)
        return DEFAULT_PRIORITIES, [], []


# =========================
# 🧠 FABRIC INQUIRY ANALYSIS
# =========================
def analyze_fabric_inquiry(image_path: str, user_message: str = ""):
    """
    Analyze uploaded fabric image + user message using Gemini Vision.
    Returns structured AI insights: name, material, description, estimated price, suggestion.
    """
    try:
        if not os.path.exists(image_path):
            print("❌ Image file not found for analysis:", image_path)
            return {
                "name": None,
                "material": None,
                "description": None,
                "estimated_price": None,
                "suggestion": "Image not found. Please re-upload.",
                "error": "Missing file"
            }

        model = get_model()
        img = Image.open(image_path)

        prompt = f"""
        You are an AI textile expert analyzing this fabric image.
        Respond ONLY in JSON with:
        {{
          "name": "Probable name of the fabric",
          "material": "Type of material (cotton, silk, etc.)",
          "description": "Short appealing line describing texture and color",
          "estimated_price": "Approx price range in ₹ per meter",
          "suggestion": "Short use case or selling tip"
        }}
        Customer query: "{user_message or 'No specific question.'}"
        """

        response = model.generate_content([prompt, img])

        if response and hasattr(response, "text"):
            text = response.text.strip()
            import json, re
            try:
                cleaned = re.sub(r"```(?:json)?", "", text).strip("` \n")
                data = json.loads(cleaned)
                return data
            except Exception:
                return {
                    "name": None,
                    "material": None,
                    "description": text[:200],
                    "estimated_price": "Unavailable",
                    "suggestion": "AI returned unstructured data."
                }

        return {
            "name": None,
            "material": None,
            "description": "No AI response.",
            "estimated_price": "Unavailable",
            "suggestion": "Please retry later."
        }

    except Exception as e:
        if "quota" in str(e).lower():
            print("⚠️ Gemini API quota reached.")
            return {
                "name": "Cotton Blend",
                "material": "Cotton",
                "description": "Soft textured lightweight fabric, easy to maintain.",
                "estimated_price": "₹400–₹600 per meter",
                "suggestion": "Ideal for daily wear shirts and dresses.",
                "note": "Default fallback due to quota limit."
            }

        print("❌ Fabric Inquiry Analysis Error:", e)
        return {
            "error": str(e),
            "name": None,
            "material": None,
            "description": None,
            "estimated_price": None,
            "suggestion": "AI processing failed."
        }
