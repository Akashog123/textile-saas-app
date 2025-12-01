# backend/services/ai_service.py
"""
AI Service Layer - Provider-agnostic AI operations
Supports multiple AI providers (Gemini, NVIDIA) configured via environment
Includes response caching to minimize redundant API calls.
"""

import os
import re
import hashlib
import time
import pandas as pd
import traceback
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple
from services.ai_providers import get_provider
from services.prophet_service import prophet_manager


# Default Fallback Responses
DEFAULT_CAPTION = "Elegant design for every occasion!"
DEFAULT_SUMMARY = "Steady growth observed across key regions with strong fabric demand."
DEFAULT_RECOMMENDATION = "Maintain higher silk stock in northern regions; expand cotton offerings in the east."
DEFAULT_PRIORITIES = [
    {"title": "Scale up high-demand fabrics", "detail": "Increase production for top performers.", "level": "increase"},
    {"title": "Maintain stable cotton blends", "detail": "Keep inventory consistent for steady sellers.", "level": "maintain"},
    {"title": "Reduce low-selling SKUs", "detail": "Optimize resources by limiting underperformers.", "level": "reduce"},
]


# ============================================================================
# AI Response Cache
# ============================================================================
class AIResponseCache:
    """
    In-memory cache for AI API responses to minimize redundant calls.
    Uses TTL-based expiration and input hashing for cache keys.
    """
    def __init__(self, ttl_seconds: int = 1800, max_size: int = 100):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds  # 30 minutes default
        self.max_size = max_size
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function name and arguments."""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, func_name: str, *args, **kwargs) -> Optional[Any]:
        """Get cached response if valid."""
        key = self._generate_key(func_name, *args, **kwargs)
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                print(f"[AI Cache HIT] {func_name}")
                return value
            else:
                del self._cache[key]  # Expired
        return None
    
    def set(self, func_name: str, value: Any, *args, **kwargs):
        """Store response in cache."""
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        key = self._generate_key(func_name, *args, **kwargs)
        self._cache[key] = (value, time.time())
        print(f"[AI Cache SET] {func_name}")
    
    def clear(self):
        """Clear all cached responses."""
        self._cache.clear()


# Global cache instance
ai_cache = AIResponseCache(ttl_seconds=1800)  # 30-minute TTL


def _limit_sentences(text: str, max_sentences: int = 4) -> str:
    """Keep AI responses within a reasonable sentence count."""
    if not text:
        return text

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return text.strip()

    truncated = sentences[:max_sentences]
    return " ".join(truncated)


def generate_ai_caption(product_name: str = None, category: str = None, price: float = None, image_path: str = None, description: str = None):
    """
    Generate AI-powered marketing captions using configured AI provider.
    Supports both image-based and text-based caption generation.
    """
    try:
        provider = get_provider()
        DEFAULT_CAPTION = "Elegant textile product for modern fashion."
        
        # Image-based caption (for single image uploads)
        if image_path and os.path.exists(image_path):
            prompt = (
                "Generate a short, catchy marketing caption (under 25 words) "
                "for this textile or fashion product image. "
                "Focus on elegance, premium tone, and emotional appeal."
            )
            
            # Add product details to the prompt if provided
            if product_name or category or description:
                details = []
                if product_name:
                    details.append(f"Product: {product_name}")
                if category:
                    details.append(f"Category: {category}")
                if description:
                    details.append(f"Description: {description}")
                
                if details:
                    prompt += f" Product details: {', '.join(details)}."
            
            try:
                result = provider.analyze_image(image_path, prompt)
                if result and result.strip():
                    return result.strip()
            except Exception as e:
                print(f"Image caption generation failed: {e}")
                return DEFAULT_CAPTION
        
        # Text-based caption (for CSV/XLSX input)
        product_name = str(product_name or "").strip()
        category = str(category or "").strip()
        price_str = str(price or "N/A")
        
        prompt = f"""
        Create a short, premium marketing caption (under 35 words)
        for a textile or fabric product.
        Product: {product_name}
        Category: {category}
        Price: ₹{price_str}
        {f'Description: {description}' if description else ''}
        Tone: Elegant, aesthetic, and festive to attract buyers.
        """
        
        try:
            result = provider.generate_text(prompt)
            if result and result.strip():
                return result.strip()
        except Exception as e:
            print(f"Text caption generation failed: {e}")
        
        return DEFAULT_CAPTION
        
    except Exception as e:
        print("AI Caption Generation Error:", e)
        return DEFAULT_CAPTION


def generate_marketing_poster(image_path: str, product_name: str = None, aspect_ratio: str = ""):
    """
    Generate AI marketing poster from uploaded image with aspect ratio support.
    Only uses AI services - no local fallbacks.
    Proper logging for debugging AI issues.
    """
    if not os.path.exists(image_path):
        print(f"[AI POSTER ERROR] Image path not found: {image_path}")
        return None, None
    
    try:
        print(f"[AI POSTER] Starting generation for: {os.path.basename(image_path)}")
        print(f"[AI POSTER] Full image path: {image_path}")
        print(f"[AI POSTER] Image exists: {os.path.exists(image_path)}")
        print(f"[AI POSTER] Image size: {os.path.getsize(image_path)} bytes")
        print(f"[AI POSTER] Aspect ratio: {aspect_ratio or 'default (16:9)'}")
        
        provider = get_provider()
        print(f"[AI POSTER] Using provider: {type(provider).__name__}")
        
        # Step 1: Analyze image to create poster prompt
        vision_prompt = (
            "Analyze this product image for a high-end marketing poster. "
            "Describe the visual elements in detail: lighting, colors, texture, and composition. "
            "Then, write a stable-diffusion style prompt that would recreate this product in a professional studio setting. "
            "Include keywords like 'cinematic lighting', '8k', 'photorealistic', 'commercial photography'."
        )
        
        try:
            print(f"[AI POSTER] Analyzing image for prompt generation...")
            banner_prompt = provider.analyze_image(image_path, vision_prompt)
            print(f"[AI POSTER] Generated prompt: {banner_prompt}")
            
            if not banner_prompt or not banner_prompt.strip():
                banner_prompt = "Professional studio photography of a premium textile product, cinematic lighting, 8k resolution, commercial aesthetic."
                print(f"[AI POSTER] Using fallback prompt: {banner_prompt}")
            else:
                # Clean up prompt if it contains "Prompt:" or similar
                if "Prompt:" in banner_prompt:
                    banner_prompt = banner_prompt.split("Prompt:")[-1].strip()
                
                # Limit prompt length to avoid API issues
                if len(banner_prompt) > 900:
                    banner_prompt = banner_prompt[:900] + "..."
                    print(f"[AI POSTER] Truncated prompt to 900 characters")
        except Exception as e:
            print(f"[AI POSTER ERROR] Prompt generation failed: {str(e)}")
            print(f"[AI POSTER ERROR] Traceback: {traceback.format_exc()}")
            banner_prompt = "Professional studio photography of a premium textile product, cinematic lighting, 8k resolution, commercial aesthetic."
        
        if product_name:
            # Create a composite prompt
            banner_prompt = f"Marketing poster for {product_name}. {banner_prompt}"
            print(f"[AI POSTER] Enhanced prompt with product name: {banner_prompt}")
        
        # Step 2: Generate poster image using AI only with aspect ratio
        return _generate_ai_poster(image_path, banner_prompt, provider, aspect_ratio)
    
    except Exception as e:
        print(f"[AI POSTER ERROR] Critical error in poster generation: {str(e)}")
        print(f"[AI POSTER ERROR] Traceback: {traceback.format_exc()}")
        return None, None


def _generate_ai_poster(image_path: str, prompt: str, provider, aspect_ratio: str = ""):
    """
    Generate poster using AI services with dual API support and aspect ratio.
    Uses original NVIDIA API for context-based, OpenAI API for text-based.
    """
    output_path = os.path.splitext(image_path)[0] + "_poster.png"
    
    try:
        print(f"[AI POSTER] Attempting AI poster generation...")
        print(f"[AI POSTER] Input image: {image_path}")
        print(f"[AI POSTER] Output path: {output_path}")
        print(f"[AI POSTER] Prompt length: {len(prompt)} characters")
        print(f"[AI POSTER] Aspect ratio: {aspect_ratio or 'default (16:9)'}")
        
        # Determine aspect ratio for generation
        generation_aspect_ratio = aspect_ratio if aspect_ratio else "16:9"
        print(f"[AI POSTER] Using aspect ratio: {generation_aspect_ratio}")
        
        # Strategy 1: Context-based generation using NVIDIA API (image + text)
        try:
            print(f"[AI POSTER] Trying context-based generation...")
            
            # Read and encode the image
            with open(image_path, "rb") as f:
                import base64
                image_data = base64.b64encode(f.read()).decode()
                image_b64 = f"data:image/jpeg;base64,{image_data}"
                print(f"[AI POSTER] Encoded image data: {len(image_data)} bytes")
            
            # Create a short, effective prompt for marketing poster
            # Extract product name more reliably
            if "for" in prompt:
                # Split on "for" and take the part after it
                parts = prompt.split("for", 1)
                product_name = parts[1].strip() if len(parts) > 1 else prompt.split(".")[0].strip()
            else:
                # Take first sentence or first 50 characters
                product_name = prompt.split(".")[0].strip() if "." in prompt else prompt[:50].strip()
            
            # Clean up the product name
            product_name = product_name.replace("Create a marketing poster for", "").strip()
            
            simple_prompt = f"{product_name[:30]} marketing poster" if len(product_name) > 30 else f"{product_name} marketing poster"
            
            print(f"[AI POSTER] Context prompt: {simple_prompt}")
            print(f"[AI POSTER] Prompt length: {len(simple_prompt)} characters")
            
            # Try context-based generation with image
            image_bytes = provider.generate_image(
                simple_prompt,
                context_image=image_b64  # Pass the base64 image
            )
            
            print(f"[AI POSTER] Generated {len(image_bytes)} bytes via context-based generation")
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"[AI POSTER SUCCESS] Context-based poster saved: {output_path}")
            return simple_prompt, output_path
            
        except Exception as e:
            print(f"[AI POSTER ERROR] Context-based generation failed: {str(e)}")
            print(f"[AI POSTER ERROR] Traceback: {traceback.format_exc()}")
            
            # Check for specific AI service issues
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                print(f"[AI POSTER ERROR] AI quota limit reached")
            elif "timeout" in error_msg:
                print(f"[AI POSTER ERROR] AI service timeout")
            elif "connection" in error_msg or "network" in error_msg:
                print(f"[AI POSTER ERROR] Network connectivity issue")
            elif "api" in error_msg or "key" in error_msg:
                print(f"[AI POSTER ERROR] API configuration issue")
            elif "422" in error_msg or "500" in error_msg:
                print(f"[AI POSTER ERROR] Context generation not supported, falling back to text-only")
            else:
                print(f"[AI POSTER ERROR] Unknown AI service error")
        
        # Strategy 2: Text-based generation using NVIDIA API (text-only fallback)
        try:
            print(f"[AI POSTER] Trying text-based generation (fallback)...")
            
            # Create a short, effective prompt for marketing poster
            # Extract product name more reliably
            if "for" in prompt:
                # Split on "for" and take the part after it
                parts = prompt.split("for", 1)
                product_name = parts[1].strip() if len(parts) > 1 else prompt.split(".")[0].strip()
            else:
                # Take first sentence or first 50 characters
                product_name = prompt.split(".")[0].strip() if "." in prompt else prompt[:50].strip()
            
            # Clean up the product name
            product_name = product_name.replace("Create a marketing poster for", "").strip()
            
            simple_prompt = f"{product_name[:30]} marketing poster" if len(product_name) > 30 else f"{product_name} marketing poster"
            
            print(f"[AI POSTER] Text-only prompt: {simple_prompt}")
            print(f"[AI POSTER] Prompt length: {len(simple_prompt)} characters")
            
            image_bytes = provider.generate_image(
                simple_prompt
                # No context_image - text-only generation
            )
            
            print(f"[AI POSTER] Generated {len(image_bytes)} bytes via text-based generation")
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"[AI POSTER SUCCESS] Text-based poster saved: {output_path}")
            return f"Text-only: {simple_prompt}", output_path
            
        except Exception as e:
            print(f"[AI POSTER ERROR] Text-based generation failed: {str(e)}")
            print(f"[AI POSTER ERROR] Traceback: {traceback.format_exc()}")
            
            # Check for specific AI service issues
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                print(f"[AI POSTER ERROR] AI quota limit reached")
            elif "timeout" in error_msg:
                print(f"[AI POSTER ERROR] AI service timeout")
            elif "connection" in error_msg or "network" in error_msg:
                print(f"[AI POSTER ERROR] Network connectivity issue")
            elif "api" in error_msg or "key" in error_msg:
                print(f"[AI POSTER ERROR] API configuration issue")
            else:
                print(f"[AI POSTER ERROR] Unknown AI service error")
    
    except Exception as e:
        print(f"[AI POSTER ERROR] Critical error in poster generation: {str(e)}")
        print(f"[AI POSTER ERROR] Traceback: {traceback.format_exc()}")
        return prompt, None
    
    # All AI strategies failed
    print(f"[AI POSTER FAILED] Unable to generate poster with AI services")
    return prompt, None


def batch_generate_posters(image_paths: list, product_names: list = None, aspect_ratio: str = "", batch_size: int = 3):
    """
    Generate multiple posters using AI services with aspect ratio and batch processing.
    Robust error handling and progress tracking.
    """
    if not product_names:
        product_names = [f"Product {i+1}" for i in range(len(image_paths))]
    
    print(f"[BATCH AI] Starting batch poster generation for {len(image_paths)} images")
    print(f"[BATCH AI] Settings: aspect_ratio={aspect_ratio}, batch_size={batch_size}")
    
    results = []
    
    # Process in batches to avoid API rate limits
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i + batch_size]
        batch_names = product_names[i:i + batch_size]
        
        print(f"[BATCH AI] Processing batch {i//batch_size + 1}: {len(batch_paths)} images")
        
        for j, (image_path, product_name) in enumerate(zip(batch_paths, batch_names)):
            try:
                print(f"[BATCH AI] Processing image {i+j+1}/{len(image_paths)}: {product_name}")
                
                # Generate AI caption for the product
                caption = generate_ai_caption(product_name, "Fashion", 1000, image_path)
                print(f"[BATCH AI] Generated caption for {product_name}")
                
                # Generate poster with aspect ratio
                prompt, poster_path = generate_marketing_poster(image_path, product_name, aspect_ratio)
                
                if poster_path:
                    results.append({
                        'success': True,
                        'poster_path': poster_path,
                        'prompt': prompt,
                        'product_name': product_name,
                        'caption': caption
                    })
                    print(f"[BATCH AI] SUCCESS: Poster generated for {product_name}")
                else:
                    results.append({
                        'success': False,
                        'error': 'Poster generation failed',
                        'product_name': product_name,
                        'caption': caption
                    })
                    print(f"[BATCH AI] FAILED: Poster generation for {product_name}")
                    
            except Exception as e:
                print(f"[BATCH AI] ERROR processing {product_name}: {str(e)}")
                print(f"[BATCH AI] Traceback: {traceback.format_exc()}")
                
                results.append({
                    'success': False,
                    'error': str(e),
                    'product_name': product_name
                })
    
    success_count = sum(1 for r in results if r['success'])
    print(f"[BATCH AI] Completed: {success_count}/{len(image_paths)} posters generated successfully")
    
    return results


def forecast_trends(df: pd.DataFrame):
    """Generate 30-day sales forecast using Prophet (AI-independent)."""
    try:
        if df is None or df.empty:
            return []
        if not {"Date", "Sales"}.issubset(df.columns):
            return []
        
        # Prepare data for optimized Prophet
        prophet_df = df[["Date", "Sales"]].copy()
        prophet_df.columns = ["ds", "y"]  # Prophet expects ds, y columns
        
        # Use optimized Prophet service
        forecast_data, metrics = prophet_manager.forecast_sales(prophet_df, periods=30)
        
        # Extract forecast values
        trend = pd.DataFrame({
            'ds': forecast_data['ds'],
            'yhat': forecast_data['yhat']
        }).tail(30)
        
        return trend.to_dict(orient="records")
    
    except Exception as e:
        print("Forecasting Error:", e)
        return []


def generate_demand_summary(region_data, top_product, engine="auto"):
    """Generate concise AI-powered regional demand summary with caching."""
    try:
        # Check cache first
        cached = ai_cache.get("demand_summary", str(region_data), str(top_product))
        if cached:
            return cached
        
        provider = get_provider()
        region_text = str(region_data)[:800]
        top_product = str(top_product or "N/A")
        
        prompt = f"""
        Analyze textile demand data:
        Regional Summary: {region_text}
        Top Product: {top_product}
        
        Write a concise business summary in 2-3 sentences (max 80 words):
        - Highlight top performing regions
        - Call out growth insights
        - Mention expected sales trend
        Keep the tone professional and analytical.
        """
        
        result = provider.generate_text(prompt)
        trimmed = _limit_sentences(result, max_sentences=4) if result else None
        summary = trimmed if trimmed and trimmed.strip() else DEFAULT_SUMMARY
        
        # Cache the result
        ai_cache.set("demand_summary", summary, str(region_data), str(top_product))
        return summary
    
    except Exception as e:
        print("AI Summary Generation Error:", e)
        return DEFAULT_SUMMARY


def generate_recommendation(region_data, trending_products, engine="auto"):
    """Generate actionable short business recommendations with caching."""
    try:
        # Check cache first
        cached = ai_cache.get("recommendation", str(region_data), str(trending_products))
        if cached:
            return cached
        
        provider = get_provider()
        region_text = str(region_data)[:500]
        trending_text = str(trending_products)[:500]
        
        prompt = f"""
        Based on regional textile demand and trending fabrics:
        Regions: {region_text}
        Trending: {trending_text}
        
        Provide 2 concise sentences (max 35 words total):
        - Inventory action to take
        - Marketing or regional strategy tweak
        Avoid bullet points and keep it actionable.
        """
        
        result = provider.generate_text(prompt)
        trimmed = _limit_sentences(result, max_sentences=4) if result else None
        recommendation = trimmed if trimmed and trimmed.strip() else DEFAULT_RECOMMENDATION
        
        # Cache the result
        ai_cache.set("recommendation", recommendation, str(region_data), str(trending_products))
        return recommendation
    
    except Exception as e:
        print("AI Recommendation Error:", e)
        return DEFAULT_RECOMMENDATION


def generate_production_priorities(df: pd.DataFrame):
    """AI-driven production scaling suggestions.
    
    Returns defaults immediately if DataFrame is empty or insufficient.
    """
    try:
        # Early return if DataFrame is empty or too small
        if df is None or df.empty or len(df) < 3:
            print("[Production Priorities] Skipping - insufficient data")
            return DEFAULT_PRIORITIES, [], []
        
        # Check for required columns
        if "Product" not in df.columns or "Sales" not in df.columns:
            print("[Production Priorities] Skipping - missing required columns (Product, Sales)")
            return DEFAULT_PRIORITIES, [], []
        
        products = df.groupby("Product")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
        
        # Skip if no meaningful product data
        if products.empty or products["Sales"].sum() < 1:
            print("[Production Priorities] Skipping - no meaningful sales data")
            return DEFAULT_PRIORITIES, [], []
        
        # Calculate real growth/decline from data if we have region info
        # Group by product and region for regional analysis
        region_data = {}
        if "Region" in df.columns:
            region_data = df.groupby(["Product", "Region"])["Sales"].sum().reset_index()
        
        # Get top region per product for display
        def get_top_region(product_name):
            if not region_data.empty if isinstance(region_data, pd.DataFrame) else not region_data:
                prod_regions = region_data[region_data["Product"] == product_name]
                if not prod_regions.empty:
                    return prod_regions.loc[prod_regions["Sales"].idxmax(), "Region"]
            return "N/A"
        
        # Calculate relative performance (% of total sales)
        total_sales = products["Sales"].sum()
        
        top_selling, underperforming = [], []
        
        # Top selling products with real data
        top_count = min(5, len(products))
        for idx, (_, row) in enumerate(products.head(top_count).iterrows()):
            market_share = (row["Sales"] / total_sales * 100) if total_sales > 0 else 0
            top_selling.append({
                "name": row["Product"],
                "growth": f"+{market_share:.1f}% share",  # market share percentage
                "region": get_top_region(row["Product"]),  # top region for this product
                "volume": f"{int(row['Sales']):,}",  # actual sales volume
                "image": None  # Will be populated by frontend from product database
            })
        
        # Underperforming products with real data
        bottom_count = min(5, len(products))
        for idx, (_, row) in enumerate(products.tail(bottom_count).iterrows()):
            market_share = (row["Sales"] / total_sales * 100) if total_sales > 0 else 0
            underperforming.append({
                "name": row["Product"],
                "region": get_top_region(row["Product"]),  # Real: top region for this product  
                "decline": f"{market_share:.1f}% share",  # Real: low market share
                "volume": f"{int(row['Sales']):,}",  # Real: actual sales volume
                "image": None  # Will be populated by frontend from product database
            })
        
        # Skip redundant AI call - data already analyzed
        # Production priorities can be derived from the data itself
        priorities = []
        if len(top_selling) > 0:
            priorities.append({
                "title": f"Scale up {top_selling[0]['name']}",
                "detail": f"Top performer with {top_selling[0]['growth']} - increase production capacity.",
                "level": "increase"
            })
        if len(products) > 2:
            mid_product = products.iloc[len(products)//2]["Product"]
            priorities.append({
                "title": f"Maintain {mid_product} inventory",
                "detail": "Steady performer - keep current stock levels.",
                "level": "maintain"
            })
        if len(underperforming) > 0:
            priorities.append({
                "title": f"Review {underperforming[0]['name']} SKU",
                "detail": f"Low performer with {underperforming[0]['decline']} - consider reducing or repositioning.",
                "level": "reduce"
            })
        
        # Use defaults if we couldn't generate enough priorities
        if len(priorities) < 3:
            priorities = DEFAULT_PRIORITIES
        
        return priorities, top_selling, underperforming
    
    except Exception as e:
        print("Production Priority Generation Error:", e)
        return DEFAULT_PRIORITIES, [], []


def analyze_fabric_inquiry(image_path: str, user_message: str = ""):
    """
    Analyze uploaded fabric image + user message using configured AI provider.
    Returns structured AI insights: name, material, description, estimated price, suggestion.
    """
    try:
        if not os.path.exists(image_path):
            print("Image file not found for analysis:", image_path)
            return {
                "name": None,
                "material": None,
                "description": None,
                "estimated_price": None,
                "suggestion": "Image not found. Please re-upload.",
                "error": "Missing file"
            }
        
        provider = get_provider()
        
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
        
        result = provider.analyze_image(image_path, prompt)
        
        if result and result.strip():
            import json, re
            try:
                # Clean JSON formatting
                cleaned = re.sub(r"```(?:json)?", "", result).strip("` \n")
                data = json.loads(cleaned)
                return data
            except Exception:
                return {
                    "name": None,
                    "material": None,
                    "description": result[:200],
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
            print("AI API quota reached.")
            return {
                "name": "Cotton Blend",
                "material": "Cotton",
                "description": "Soft textured lightweight fabric, easy to maintain.",
                "estimated_price": "₹400–₹600 per meter",
                "suggestion": "Ideal for daily wear shirts and dresses.",
                "note": "Default fallback due to quota limit."
            }
        
        print("Fabric Inquiry Analysis Error:", e)
        return {
            "error": str(e),
            "name": None,
            "material": None,
            "description": None,
            "estimated_price": None,
            "suggestion": "AI processing failed."
        }
