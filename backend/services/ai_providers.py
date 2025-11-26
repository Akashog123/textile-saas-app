# backend/services/ai_providers.py
"""
Multi-provider AI service abstraction layer
Supports: Gemini, NVIDIA APIs
"""

import os
import base64
import requests
from PIL import Image
from openai import OpenAI
from config import Config


class AIProvider:
    """Base class for AI providers"""
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        raise NotImplementedError
    
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        """Generate image from prompt"""
        raise NotImplementedError
    
    def analyze_image(self, image_path: str, prompt: str, **kwargs) -> str:
        """Analyze image with text prompt"""
        raise NotImplementedError
    
    def transcribe_audio(self, audio_data: bytes, mime_type: str, **kwargs) -> str:
        """Transcribe audio data to text"""
        raise NotImplementedError


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider"""
    
    def __init__(self):
        import google.generativeai as genai
        from google.generativeai import GenerativeModel
        
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.genai = genai
        self.GenerativeModel = GenerativeModel
        print("Gemini AI Provider initialized")
    
    def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using Gemini"""
        try:
            model_name = model or Config.AI_TEXT_MODEL
            gen_model = self.GenerativeModel(model_name)
            response = gen_model.generate_content(prompt, **kwargs)
            
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            print(f"Gemini text generation error: {e}")
            raise
    
    def generate_image(self, prompt: str, model: str = None, **kwargs) -> bytes:
        """Generate image using Gemini (if available)"""
        try:
            model_name = model or "gemini-2.5-flash-image"
            gen_model = self.GenerativeModel(model_name)
            result = gen_model.generate_content([prompt], **kwargs)
            
            for part in result.parts:
                if hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                    return part.inline_data.data
            
            raise Exception("No image data in Gemini response")
        except Exception as e:
            print(f"Gemini image generation error: {e}")
            raise
    
    def analyze_image(self, image_path: str, prompt: str, model: str = None, **kwargs) -> str:
        """Analyze image using Gemini Vision"""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            model_name = model or Config.AI_VISION_MODEL
            gen_model = self.GenerativeModel(model_name)
            img = Image.open(image_path)
            
            response = gen_model.generate_content([prompt, img], **kwargs)
            
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            print(f"Gemini image analysis error: {e}")
            raise
    
    def transcribe_audio(self, audio_data: bytes, mime_type: str, **kwargs) -> str:
        """Transcribe audio data using Gemini"""
        try:
            model_name = "gemini-2.5-flash"
            gen_model = self.GenerativeModel(model_name)
            
            response = gen_model.generate_content([
                "Transcribe customer voice input for textile store search. "
                "Focus on fabric types, store locations, and textile requirements.",
                {
                    "mime_type": mime_type,
                    "data": audio_data
                }
            ], **kwargs)
            
            if response and hasattr(response, "text") and response.text:
                transcript = response.text.strip()
                if not transcript or len(transcript) < 2:
                    raise ValueError("Invalid transcription")
                return transcript
            
            raise ValueError("No transcription returned")
        except Exception as e:
            print(f"Gemini audio transcription error: {e}")
            raise


class NVIDIAProvider(AIProvider):
    """NVIDIA AI API Provider"""
    
    def __init__(self):
        if not Config.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY not configured")
        
        # Initialize OpenAI client for NVIDIA text API
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=Config.NVIDIA_API_KEY
        )
        
        # NVIDIA image generation endpoint
        self.image_endpoint = "https://ai.api.nvidia.com/v1/genai/"
        
        print("NVIDIA AI Provider initialized")
    
    def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using NVIDIA"""
        try:
            model_name = model or Config.AI_TEXT_MODEL
            
            # Extract temperature and other params
            temperature = kwargs.get("temperature", 0.6)
            top_p = kwargs.get("top_p", 0.7)
            max_tokens = kwargs.get("max_tokens", 4096)
            
            completion = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Check for reasoning content
            reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
            if reasoning:
                print(f"[NVIDIA Model Reasoning]: {reasoning[:200]}...")
            
            return completion.choices[0].message.content
        except Exception as e:
            print(f"NVIDIA text generation error: {e}")
            raise
    
    def generate_image(self, prompt: str, model: str = None, **kwargs) -> bytes:
        """Generate image using NVIDIA (Flux.1-Kontext-Dev)"""
        try:
            model_name = model or Config.AI_IMAGE_MODEL
            invoke_url = f"{self.image_endpoint}{model_name}"
            
            headers = {
                "Authorization": f"Bearer {Config.NVIDIA_API_KEY}",
                "Accept": "application/json",
            }
            
            payload = {
                "prompt": prompt,
                "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
                "steps": kwargs.get("steps", 30),
                "cfg_scale": kwargs.get("cfg_scale", 3.5),
                "seed": kwargs.get("seed", 0)
            }
            
            # Add image for context if provided
            if "context_image" in kwargs:
                payload["image"] = kwargs["context_image"]
                payload["aspect_ratio"] = "match_input_image"
            
            response = requests.post(invoke_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            response_body = response.json()
            
            # Extract image data from response
            if "image" in response_body:
                # Assuming base64 encoded image
                image_data = base64.b64decode(response_body["image"])
                return image_data
            
            raise Exception("No image data in NVIDIA response")
        except Exception as e:
            print(f"NVIDIA image generation error: {e}")
            raise
    
    def analyze_image(self, image_path: str, prompt: str, model: str = None, **kwargs) -> str:
        """
        Analyze image using NVIDIA vision models
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            model_name = model or Config.AI_VISION_MODEL
            analysis_prompt = f"{prompt}\n\n[Image analysis for: {os.path.basename(image_path)}]"
            
            return self.generate_text(analysis_prompt, model=model_name, **kwargs)
        except Exception as e:
            print(f"NVIDIA image analysis error: {e}")
            raise
    
    def transcribe_audio(self, audio_data: bytes, mime_type: str, **kwargs) -> str:
        """
        Transcribe audio using NVIDIA's Whisper model
        """
        try:
            # NVIDIA Whisper endpoint
            whisper_url = "https://api.nvc.nvidia.com/v1/nvidia/whisper/asr"
            
            headers = {
                "Authorization": f"Bearer {Config.NVIDIA_API_KEY}",
                "Content-Type": "application/json",
            }
            
            # Prepare the request for Whisper
            import base64
            
            # Encode audio data as base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "model": "openai/whisper-large-v3",
                "audio": f"data:{mime_type};base64,{audio_b64}",
                "language": "en",  # Default to English
                "response_format": "text",
                "temperature": kwargs.get("temperature", 0.0)
            }
            
            response = requests.post(whisper_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract transcription from response
            if "text" in result:
                transcript = result["text"].strip()
                if not transcript or len(transcript) < 2:
                    raise ValueError("Invalid transcription")
                return transcript
            elif "transcription" in result:
                transcript = result["transcription"].strip()
                if not transcript or len(transcript) < 2:
                    raise ValueError("Invalid transcription")
                return transcript
            else:
                raise ValueError("No transcription in NVIDIA Whisper response")
                
        except Exception as e:
            print(f"NVIDIA Whisper transcription error: {e}")
            # Fallback to Gemini if available
            if Config.GEMINI_API_KEY:
                print("NVIDIA provider falling back to Gemini for audio transcription")
                gemini_provider = GeminiProvider()
                return gemini_provider.transcribe_audio(audio_data, mime_type, **kwargs)
            else:
                raise NotImplementedError(f"NVIDIA Whisper transcription failed: {str(e)}")


# Provider Factory
def get_ai_provider() -> AIProvider:
    """Get the configured AI provider"""
    provider_name = Config.AI_PROVIDER
    
    if provider_name == "nvidia":
        return NVIDIAProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        print(f"Unknown AI provider: {provider_name}, falling back to Gemini")
        return GeminiProvider()


# Singleton instance
_provider_instance = None

def get_provider() -> AIProvider:
    """Get or create the AI provider singleton"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = get_ai_provider()
    return _provider_instance
