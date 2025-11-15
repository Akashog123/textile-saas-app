from flask import Blueprint, request, jsonify
from models.model import StoreRegion
import tempfile
import google.generativeai as genai
import json
import re

ai_bp = Blueprint("ai", __name__, url_prefix="/")

genai.configure(api_key="AIzaSyB4124DMFesEd6NXYhzsk6BQBIuKgZmnog")
model = genai.GenerativeModel("gemini-2.5-flash")

@ai_bp.route('/', methods=['POST'])
def ai_find_stores():
    data = request.form or request.get_json(silent=True)
    user_prompt = data.get("prompt") if data else None
    audio_file = request.files.get("voice_note")

    if not user_prompt and not audio_file:
        return jsonify({"error": "Provide prompt or voice file"}), 400

    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio_path = tmp.name
            audio_file.save(audio_path)

        resp = model.generate_content([
            "Transcribe for textile store search.",
            {"mime_type":"audio/wav","data":open(audio_path,"rb").read()}
        ])
        user_prompt = resp.text.strip()

    stores = StoreRegion.query.all()
    store_data = [{
        "StoreName": s.StoreName,
        "City": s.City,
        "Product_description": s.Product_description,
        "Latitude": s.Latitude,
        "Longitude": s.Longitude,
        "RegionName": s.RegionName,
        "ImagePath": s.ImagePath
    } for s in stores]

    prompt = f"""
    Customer query: "{user_prompt}"
    Stores: {store_data}
    Return JSON array of matching stores.
    """

    ai_resp = model.generate_content(prompt).text.strip()
    match = re.search(r'\[.*\]', ai_resp, re.DOTALL)
    result = json.loads(match.group(0)) if match else []

    return jsonify({
        "matches_found": len(result),
        "matching_stores": result
    })
