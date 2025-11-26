import os
import tempfile
import json
import re
import logging

from flask import Blueprint, request, jsonify

from config import Config
from models.model import StoreRegion
from utils.audio_validation import validate_voice_file, get_audio_metadata
from services.ai_providers import get_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai_find_stores", __name__)

# Global AI provider
ai_provider = None
try:
    ai_provider = get_provider()
    logger.info(f"AI Provider initialized: {Config.AI_PROVIDER}")
except Exception as e:
    logger.error(f"Failed to initialize AI provider: {e}")
    ai_provider = None


def _transcribe_audio(file_storage):
    """Transcribe audio file with comprehensive validation and format support"""
    if not ai_provider:
        raise RuntimeError("AI provider not configured")

    # Validate audio file
    is_valid, message, metadata = validate_voice_file(file_storage, max_size_mb=10)
    if not is_valid:
        raise ValueError(f"Invalid audio file: {message}")
    
    logger.info(f"Processing audio file: {metadata.get('filename', 'unknown')} "
               f"({metadata.get('size_mb', 0):.2f}MB, {metadata.get('file_extension', 'unknown')})")

    # Get proper MIME type
    mime_type = metadata.get('content_type') or metadata.get('expected_mime_type')
    if not mime_type or mime_type == 'unknown':
        mime_type = 'audio/webm'  # Default fallback
    
    # Create temporary file with proper extension
    file_ext = metadata.get('file_extension', '.webm')
    suffix = os.path.splitext(file_storage.filename or f"voice_note{file_ext}")[1] or file_ext
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    
    try:
        # Save uploaded file
        file_storage.save(tmp_file.name)
        
        # Read audio data
        with open(tmp_file.name, "rb") as audio_fp:
            audio_data = audio_fp.read()
        
        # Log transcription attempt
        logger.info(f"Transcribing audio with {Config.AI_PROVIDER} Whisper: {len(audio_data)} bytes, MIME: {mime_type}")
        
        # Transcribe with global AI provider
        transcript = ai_provider.transcribe_audio(audio_data, mime_type)
        
        logger.info(f"Transcription successful: {len(transcript)} characters")
        return transcript
        
    finally:
        # Cleanup temporary file
        tmp_path = tmp_file.name
        tmp_file.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.debug(f"Cleaned up temporary file: {tmp_path}")
def _parse_ai_matches(ai_text):
    """
    Extract JSON array from AI response safely.
    AI sometimes returns text + JSON, so we isolate the JSON part.
    """
    try:
        # Try direct JSON first
        return json.loads(ai_text)
    except json.JSONDecodeError:
        # Fallback: extract JSON array using regex
        match = re.search(r"\[.*\]", ai_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return []
    return []


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
    audio_file = request.files.get("voice") or request.files.get("voice_note")

    if not user_prompt and not audio_file:
        return jsonify({
            "status": "error",
            "message": "Provide either a text prompt or a voice_note file."
        }), 400

    if audio_file:
        if not ai_provider:
            return jsonify({
                "status": "error",
                "message": "AI provider not configured for voice transcription"
            }), 503
        
        try:
            # Validate audio file before processing
            is_valid, message, metadata = validate_voice_file(audio_file, max_size_mb=10)
            if not is_valid:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid audio file: {message}",
                    "metadata": metadata
                }), 400
            
            user_prompt = _transcribe_audio(audio_file)
            logger.info(f"Audio transcription completed: {len(user_prompt)} characters")
            
        except ValueError as ve:
            logger.error(f"Audio validation error: {str(ve)}")
            return jsonify({
                "status": "error",
                "message": f"Audio validation failed: {str(ve)}"
            }), 400
        except RuntimeError as re:
            logger.error(f"AI provider runtime error: {str(re)}")
            return jsonify({
                "status": "error", 
                "message": f"AI provider error: {str(re)}"
            }), 503
        except Exception as exc:
            logger.error(f"Transcription error: {str(exc)}")
            return jsonify({
                "status": "error",
                "message": f"Could not transcribe audio: {str(exc)}"
            }), 500

    if not ai_provider:
        return jsonify({
            "status": "error",
            "message": f"AI provider not configured; configure {Config.AI_PROVIDER} provider to use this endpoint."
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
        ai_resp_text = ai_provider.generate_text(prompt)
        matches = _parse_ai_matches(ai_resp_text)
    except Exception as exc:
        logger.error(f"[AI Find Stores] {Config.AI_PROVIDER} error:", exc)
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
