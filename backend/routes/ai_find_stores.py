import os
import tempfile
import json
import re

import google.generativeai as genai
from flask import Blueprint, request, jsonify

from config import Config
from models.model import StoreRegion

ai_bp = Blueprint("ai_find_stores", __name__)

GEMINI_API_KEY = Config.GEMINI_API_KEY
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")


def _transcribe_audio(file_storage):
    if not model:
        raise RuntimeError("Gemini model is not configured")

    suffix = os.path.splitext(file_storage.filename or "voice_note.wav")[1] or ".wav"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        file_storage.save(tmp_file.name)
        with open(tmp_file.name, "rb") as audio_fp:
            resp = model.generate_content([
                "Transcribe customer voice input for textile store search.",
                {
                    "mime_type": file_storage.mimetype or "audio/wav",
                    "data": audio_fp.read()
                }
            ])
        return (resp.text or "").strip()
    finally:
        tmp_path = tmp_file.name
        tmp_file.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@ai_bp.route("/", methods=["POST"])
def ai_find_stores():
    """Find matching textile stores from text prompt or audio clip.
    ---
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            properties:
              prompt:
                type: string
                description: Customer requirement description
        multipart/form-data:
          schema:
            type: object
            properties:
              prompt:
                type: string
                description: Customer requirement description
              voice_note:
                type: string
                format: binary
                description: Voice note audio file
    responses:
      '200':
        description: Matching stores returned
      '400':
        description: Missing prompt and voice note
      '503':
        description: AI key missing
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    user_prompt = (data.get("prompt") or "").strip()
    audio_file = request.files.get("voice_note")

    if not user_prompt and not audio_file:
        return jsonify({
            "status": "error",
            "message": "Provide either a text prompt or a voice_note file."
        }), 400

    if audio_file:
        if not GEMINI_API_KEY:
            return jsonify({
                "status": "error",
                "message": "Voice transcription requires GEMINI_API_KEY to be configured."
            }), 503
        try:
            user_prompt = _transcribe_audio(audio_file)
        except Exception as exc:
            return jsonify({
                "status": "error",
                "message": f"Could not transcribe audio: {exc}"
            }), 500

    if not GEMINI_API_KEY:
        return jsonify({
            "status": "error",
            "message": "Gemini AI key is not configured; enable GEMINI_API_KEY to use this endpoint."
        }), 503

    stores = StoreRegion.query.all()
    if not stores:
        return jsonify({
            "status": "success",
            "matches_found": 0,
            "matching_stores": [],
            "message": "No store inventory available."
        }), 200

    store_data = [{
        "StoreName": s.StoreName,
        "City": s.City,
        "Product_description": s.Product_description,
        "Latitude": s.Latitude,
        "Longitude": s.Longitude,
        "RegionName": s.RegionName,
        "ImagePath": s.ImagePath
    } for s in stores]

    prompt = (
        "You are a helpful assistant for textile buyers.\n"
        f"Customer query: "
        f"{user_prompt}.\n"
        "Return a JSON array of stores from the provided list that best match the needs.\n"
        "Include StoreName, City, RegionName, Product_description, Latitude, Longitude, ImagePath,"
        " and a short reason field."
        f"\nStores: {store_data[:50]}"
    )

    try:
        ai_resp = model.generate_content(prompt)
        matches = _parse_ai_matches(ai_resp.text if ai_resp else "")
    except Exception as exc:
        print("[AI Find Stores] Gemini error:", exc)
        matches = []

    if not matches and user_prompt:
        fallback = []
        prompt_lower = user_prompt.lower()
        for store in store_data:
            haystack = " ".join(filter(None, [
                store.get("StoreName"),
                store.get("City"),
                store.get("RegionName"),
                store.get("Product_description")
            ])).lower()
            if prompt_lower in haystack:
                store_copy = store.copy()
                store_copy["reason"] = "Matched via keyword search fallback."
                fallback.append(store_copy)
        matches = fallback

    return jsonify({
        "status": "success",
        "message": "Matching stores identified" if matches else "No direct AI matches; returning fallback results.",
        "matches_found": len(matches),
        "matching_stores": matches
    }), 200
