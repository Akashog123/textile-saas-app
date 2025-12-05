import os
import tempfile
import logging

from flask import Blueprint, request, jsonify

from config import Config
from models.model import Product
from utils.audio_validation import validate_voice_file, get_audio_metadata
from services.ai_providers import get_provider

# Import semantic search for product matching
try:
    from services.search_service import semantic_search_products
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

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
    
    # Debug logging
    logger.info(f"AI Find Stores - Form data: {request.form.to_dict()}")
    logger.info(f"AI Find Stores - Files: {list(request.files.keys())}")
    logger.info(f"AI Find Stores - Prompt: '{user_prompt}', Audio file: {audio_file}")

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

    # Search for matching products using semantic search (skip store location matching)
    matching_products = []
    extracted_filters = {}
    logger.info(f"[Product Search] SEMANTIC_SEARCH_AVAILABLE={SEMANTIC_SEARCH_AVAILABLE}, user_prompt='{user_prompt[:100] if user_prompt else 'None'}...'")
    
    if user_prompt and SEMANTIC_SEARCH_AVAILABLE:
        try:
            search_result = semantic_search_products(
                query=user_prompt,
                limit=20
            )
            matching_products = search_result.get('products', [])
            extracted_filters = search_result.get('filters', {})
            logger.info(f"Found {len(matching_products)} matching products for: {user_prompt[:50]}...")
        except Exception as e:
            logger.error(f"Product search error: {e}", exc_info=True)
            matching_products = []
    elif user_prompt and not SEMANTIC_SEARCH_AVAILABLE:
        logger.warning("[Product Search] Semantic search not available, falling back to text search")
        # Fallback to basic text search
        try:
            from models.model import Product
            search_terms = user_prompt.lower().split()[:5]
            from sqlalchemy import or_
            query_obj = Product.query.filter(Product.is_active == True)
            for term in search_terms:
                pattern = f'%{term}%'
                query_obj = query_obj.filter(
                    or_(
                        Product.name.ilike(pattern),
                        Product.category.ilike(pattern),
                        Product.description.ilike(pattern)
                    )
                )
            products = query_obj.limit(20).all()
            matching_products = [p.to_card_dict() for p in products]
            logger.info(f"Text search found {len(matching_products)} products")
        except Exception as e:
            logger.error(f"Fallback text search error: {e}")
            matching_products = []

    logger.info(f"[Response] transcript='{user_prompt[:50] if user_prompt else ''}...', products={len(matching_products)}")
    
    return jsonify({
        "status": "success",
        "message": "Matching products found" if matching_products else "No matching products found.",
        "transcript": user_prompt,  # Return the transcribed/original prompt for frontend use
        "products": matching_products,
        "products_found": len(matching_products),
        "filters": extracted_filters
    }), 200
