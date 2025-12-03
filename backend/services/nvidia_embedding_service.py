# backend/services/nvidia_embedding_service.py
"""
NVIDIA NIM Cloud Embedding Service
Provides cloud-based text and image embeddings using NVIDIA's NIM API.
- Text Embeddings: nvidia/nv-embedqa-e5-v5
- Image Embeddings: nvidia/nvclip

This replaces local PyTorch/sentence-transformers with efficient cloud APIs.
"""

import os
import io
import base64
import requests
import numpy as np
from typing import Dict, Any, Optional, List, Union
from PIL import Image

from config import Config


# ============================================================================
# CONFIGURATION
# ============================================================================

NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_EMBEDDING_ENDPOINT = f"{NVIDIA_API_BASE_URL}/embeddings"

# Model IDs
TEXT_EMBEDDING_MODEL = os.getenv("NVIDIA_TEXT_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
IMAGE_EMBEDDING_MODEL = os.getenv("NVIDIA_IMAGE_EMBEDDING_MODEL", "nvidia/nvclip")

# Text embedding dimension for nv-embedqa-e5-v5 (1024 dimensions)
TEXT_EMBEDDING_DIM = 1024

# Image embedding dimension for nvclip (1024 dimensions)
IMAGE_EMBEDDING_DIM = 1024

# API request settings
REQUEST_TIMEOUT = 30
MAX_BATCH_SIZE = 50  # Max texts per batch request
MAX_TEXT_LENGTH = 8192  # Max tokens per text


# ============================================================================
# NVIDIA TEXT EMBEDDING SERVICE
# ============================================================================

class NVIDIATextEmbeddingService:
    """
    Cloud-based text embedding using NVIDIA's nv-embedqa-e5-v5 model.
    
    Features:
    - High-quality embeddings for semantic search
    - input_type differentiation (passage vs query) for better accuracy
    - Batch processing support
    - Automatic truncation handling
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.api_key = Config.NVIDIA_API_KEY
        self.model = TEXT_EMBEDDING_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._initialized = True
        
        if self.api_key:
            print(f"[NVIDIA Text Embedding] Initialized with model: {self.model}")
        else:
            print("[NVIDIA Text Embedding] No API key configured - service unavailable")
    
    @property
    def available(self) -> bool:
        """Check if service is available."""
        return bool(self.api_key)
    
    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension."""
        return TEXT_EMBEDDING_DIM
    
    def encode(
        self, 
        texts: List[str], 
        input_type: str = "passage",
        show_progress: bool = False
    ) -> Optional[np.ndarray]:
        """
        Encode multiple texts to embeddings.
        
        Args:
            texts: List of texts to encode
            input_type: 'passage' for indexing documents, 'query' for search queries
            show_progress: Not used (for API compatibility)
            
        Returns:
            numpy array of embeddings or None if failed
        """
        if not self.available:
            print("[NVIDIA Text Embedding] Service not available")
            return None
        
        if not texts:
            return np.array([]).astype('float32')
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            
            try:
                payload = {
                    "input": batch,
                    "model": self.model,
                    "input_type": input_type,
                    "encoding_format": "float",
                    "truncate": "END"  # Truncate from end if too long
                }
                
                response = requests.post(
                    NVIDIA_EMBEDDING_ENDPOINT,
                    headers=self.headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code != 200:
                    print(f"[NVIDIA Text Embedding] API error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                # Extract embeddings from response
                batch_embeddings = [item["embedding"] for item in data.get("data", [])]
                all_embeddings.extend(batch_embeddings)
                
            except requests.RequestException as e:
                print(f"[NVIDIA Text Embedding] Request error: {e}")
                return None
            except (KeyError, ValueError) as e:
                print(f"[NVIDIA Text Embedding] Parse error: {e}")
                return None
        
        return np.array(all_embeddings).astype('float32')
    
    def encode_single(self, text: str, input_type: str = "query") -> Optional[np.ndarray]:
        """
        Encode single text to embedding.
        
        Args:
            text: Text to encode
            input_type: 'passage' for indexing, 'query' for search queries
            
        Returns:
            numpy array of embedding or None if failed
        """
        result = self.encode([text], input_type=input_type)
        return result[0] if result is not None and len(result) > 0 else None
    
    def encode_passages(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encode texts as passages (for indexing)."""
        return self.encode(texts, input_type="passage")
    
    def encode_query(self, text: str) -> Optional[np.ndarray]:
        """Encode text as query (for searching)."""
        return self.encode_single(text, input_type="query")


# ============================================================================
# NVIDIA IMAGE EMBEDDING SERVICE
# ============================================================================

class NVIDIAImageEmbeddingService:
    """
    Cloud-based image embedding using NVIDIA's NVCLIP model.
    
    Features:
    - Multimodal embeddings (image + text in same space)
    - Support for image files, URLs, and base64
    - Compatible with existing FAISS indices
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.api_key = Config.NVIDIA_API_KEY
        self.model = IMAGE_EMBEDDING_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._initialized = True
        
        if self.api_key:
            print(f"[NVIDIA Image Embedding] Initialized with model: {self.model}")
        else:
            print("[NVIDIA Image Embedding] No API key configured - service unavailable")
    
    @property
    def available(self) -> bool:
        """Check if service is available."""
        return bool(self.api_key)
    
    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension."""
        return IMAGE_EMBEDDING_DIM
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        # Ensure RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large (max 1024x1024 for API efficiency)
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _create_image_input(self, image_b64: str) -> str:
        """Create NVCLIP-compatible input format."""
        # NVCLIP accepts base64 images with data URI format
        return f"data:image/jpeg;base64,{image_b64}"
    
    def encode_image(self, image: Image.Image) -> Optional[np.ndarray]:
        """
        Encode single PIL Image to embedding.
        
        Args:
            image: PIL Image object
            
        Returns:
            numpy array of embedding or None if failed
        """
        if not self.available:
            print("[NVIDIA Image Embedding] Service not available")
            return None
        
        try:
            # Convert image to base64
            image_b64 = self._image_to_base64(image)
            image_input = self._create_image_input(image_b64)
            
            payload = {
                "input": [image_input],
                "model": self.model,
                "encoding_format": "float"
            }
            
            response = requests.post(
                NVIDIA_EMBEDDING_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                print(f"[NVIDIA Image Embedding] API error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding")
            
            if embedding is None:
                print("[NVIDIA Image Embedding] No embedding in response")
                return None
            
            embedding = np.array(embedding).astype('float32')
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except requests.RequestException as e:
            print(f"[NVIDIA Image Embedding] Request error: {e}")
            return None
        except Exception as e:
            print(f"[NVIDIA Image Embedding] Error: {e}")
            return None
    
    def encode_image_file(self, file_storage) -> Optional[np.ndarray]:
        """
        Encode image from file storage object.
        
        Args:
            file_storage: Flask FileStorage or file-like object
            
        Returns:
            numpy array of embedding or None if failed
        """
        try:
            image = Image.open(file_storage)
            return self.encode_image(image)
        except Exception as e:
            print(f"[NVIDIA Image Embedding] File read error: {e}")
            return None
    
    def encode_image_url(self, url: str) -> Optional[np.ndarray]:
        """
        Encode image from URL.
        
        Args:
            url: Image URL
            
        Returns:
            numpy array of embedding or None if failed
        """
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            return self.encode_image(image)
        except Exception as e:
            print(f"[NVIDIA Image Embedding] URL fetch error: {e}")
            return None
    
    def encode_image_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Encode image from bytes.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            numpy array of embedding or None if failed
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return self.encode_image(image)
        except Exception as e:
            print(f"[NVIDIA Image Embedding] Bytes read error: {e}")
            return None
    
    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Encode text using NVCLIP (for text-to-image search).
        
        NVCLIP supports multimodal embeddings - text and images in the same space.
        
        Args:
            text: Text to encode
            
        Returns:
            numpy array of embedding or None if failed
        """
        if not self.available:
            print("[NVIDIA Image Embedding] Service not available")
            return None
        
        try:
            payload = {
                "input": [text],
                "model": self.model,
                "encoding_format": "float"
            }
            
            response = requests.post(
                NVIDIA_EMBEDDING_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                print(f"[NVIDIA Image Embedding] API error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding")
            
            if embedding is None:
                return None
            
            embedding = np.array(embedding).astype('float32')
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            print(f"[NVIDIA Image Embedding] Text encode error: {e}")
            return None


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Singleton instances - lazy initialized
_nvidia_text_embedding: Optional[NVIDIATextEmbeddingService] = None
_nvidia_image_embedding: Optional[NVIDIAImageEmbeddingService] = None


def get_nvidia_text_embedding_service() -> NVIDIATextEmbeddingService:
    """Get or create NVIDIA text embedding service."""
    global _nvidia_text_embedding
    if _nvidia_text_embedding is None:
        _nvidia_text_embedding = NVIDIATextEmbeddingService()
    return _nvidia_text_embedding


def get_nvidia_image_embedding_service() -> NVIDIAImageEmbeddingService:
    """Get or create NVIDIA image embedding service."""
    global _nvidia_image_embedding
    if _nvidia_image_embedding is None:
        _nvidia_image_embedding = NVIDIAImageEmbeddingService()
    return _nvidia_image_embedding


# ============================================================================
# HYBRID EMBEDDING SERVICE (Cloud + Local Fallback)
# ============================================================================

class HybridEmbeddingService:
    """
    Hybrid embedding service that uses NVIDIA cloud APIs with local fallback.
    
    Priority:
    1. NVIDIA Cloud API (if API key available)
    2. Local sentence-transformers (fallback)
    
    This ensures the system works even without cloud connectivity.
    """
    
    def __init__(self, prefer_cloud: bool = True):
        self.prefer_cloud = prefer_cloud
        self._nvidia_service = None
        self._local_service = None
        self._initialized = False
    
    def _init_services(self):
        """Lazy initialize services."""
        if self._initialized:
            return
        
        if self.prefer_cloud:
            self._nvidia_service = get_nvidia_text_embedding_service()
        
        # Try to import local fallback
        try:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[Hybrid Embedding] Local fallback model loaded")
        except ImportError:
            self._local_model = None
            print("[Hybrid Embedding] Local fallback not available")
        
        self._initialized = True
    
    @property
    def available(self) -> bool:
        """Check if any embedding service is available."""
        self._init_services()
        return (self._nvidia_service and self._nvidia_service.available) or self._local_model is not None
    
    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension based on active service."""
        self._init_services()
        if self._nvidia_service and self._nvidia_service.available:
            return TEXT_EMBEDDING_DIM  # 1024 for NVIDIA
        return 384  # Local model dimension
    
    @property
    def is_cloud(self) -> bool:
        """Check if using cloud service."""
        self._init_services()
        return self._nvidia_service is not None and self._nvidia_service.available
    
    def encode(
        self, 
        texts: List[str], 
        input_type: str = "passage",
        show_progress: bool = False
    ) -> Optional[np.ndarray]:
        """Encode texts with cloud or local fallback."""
        self._init_services()
        
        # Try NVIDIA cloud first
        if self._nvidia_service and self._nvidia_service.available:
            result = self._nvidia_service.encode(texts, input_type=input_type)
            if result is not None:
                return result
            print("[Hybrid Embedding] Cloud failed, trying local fallback...")
        
        # Local fallback
        if self._local_model is not None:
            try:
                embeddings = self._local_model.encode(texts, show_progress_bar=show_progress)
                return np.array(embeddings).astype('float32')
            except Exception as e:
                print(f"[Hybrid Embedding] Local encoding error: {e}")
        
        return None
    
    def encode_single(self, text: str, input_type: str = "query") -> Optional[np.ndarray]:
        """Encode single text with cloud or local fallback."""
        result = self.encode([text], input_type=input_type)
        return result[0] if result is not None and len(result) > 0 else None


class HybridImageEmbeddingService:
    """
    Hybrid image embedding service that uses NVIDIA NVCLIP with lightweight local fallback.
    
    Priority:
    1. NVIDIA NVCLIP Cloud API (if API key available)
    2. Lightweight PIL-based color histogram features (fallback, no heavy dependencies)
    """
    
    LOCAL_EMBEDDING_DIM = 768  # Color histogram features
    
    def __init__(self, prefer_cloud: bool = True):
        self.prefer_cloud = prefer_cloud
        self._nvidia_service = None
        self._use_local_fallback = False
        self._initialized = False
    
    def _init_services(self):
        """Lazy initialize services."""
        if self._initialized:
            return
        
        if self.prefer_cloud:
            self._nvidia_service = get_nvidia_image_embedding_service()
        
        # Enable lightweight fallback if cloud not available
        if self._nvidia_service is None or not self._nvidia_service.available:
            self._use_local_fallback = True
            print("[Hybrid Image Embedding] Using lightweight PIL-based features as fallback")
        
        self._initialized = True
    
    def _extract_pil_features(self, image: Image.Image) -> np.ndarray:
        """
        Extract lightweight features using PIL only (no heavy ML dependencies).
        Creates a 768-dim feature vector from color histograms.
        """
        # Ensure RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize for consistency
        image = image.resize((224, 224))
        
        # Extract color histogram for each channel
        r, g, b = image.split()
        
        # Get histograms (256 bins each)
        hist_r = np.array(r.histogram(), dtype=np.float32)
        hist_g = np.array(g.histogram(), dtype=np.float32)
        hist_b = np.array(b.histogram(), dtype=np.float32)
        
        # Normalize histograms
        hist_r = hist_r / (hist_r.sum() + 1e-8)
        hist_g = hist_g / (hist_g.sum() + 1e-8)
        hist_b = hist_b / (hist_b.sum() + 1e-8)
        
        # Concatenate to form feature vector (768 dims)
        features = np.concatenate([hist_r, hist_g, hist_b])
        
        # L2 normalize
        features = features / (np.linalg.norm(features) + 1e-8)
        
        return features.astype('float32')
    
    @property
    def available(self) -> bool:
        """Check if any embedding service is available."""
        self._init_services()
        return (self._nvidia_service and self._nvidia_service.available) or self._use_local_fallback
    
    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension based on active service."""
        self._init_services()
        if self._nvidia_service and self._nvidia_service.available:
            return IMAGE_EMBEDDING_DIM  # 1024 for NVCLIP
        return self.LOCAL_EMBEDDING_DIM  # 768 for PIL histogram
    
    @property
    def is_cloud(self) -> bool:
        """Check if using cloud service."""
        self._init_services()
        return self._nvidia_service is not None and self._nvidia_service.available
    
    def encode_image(self, image: Image.Image) -> Optional[np.ndarray]:
        """Encode image with cloud or local fallback."""
        self._init_services()
        
        # Try NVIDIA cloud first
        if self._nvidia_service and self._nvidia_service.available:
            result = self._nvidia_service.encode_image(image)
            if result is not None:
                return result
            print("[Hybrid Image Embedding] Cloud failed, trying local fallback...")
        
        # Lightweight local fallback using PIL
        if self._use_local_fallback:
            try:
                return self._extract_pil_features(image)
            except Exception as e:
                print(f"[Hybrid Image Embedding] Local encoding error: {e}")
        
        return None
    
    def encode_image_file(self, file_storage) -> Optional[np.ndarray]:
        """Encode image from file storage."""
        try:
            image = Image.open(file_storage)
            return self.encode_image(image)
        except Exception as e:
            print(f"[Hybrid Image Embedding] File read error: {e}")
            return None
    
    def encode_image_url(self, url: str) -> Optional[np.ndarray]:
        """Encode image from URL."""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            return self.encode_image(image)
        except Exception as e:
            print(f"[Hybrid Image Embedding] URL fetch error: {e}")
            return None


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_text_embedding_service(use_cloud: bool = True) -> Union[NVIDIATextEmbeddingService, HybridEmbeddingService]:
    """
    Create text embedding service based on configuration.
    
    Args:
        use_cloud: If True, prefer cloud service with local fallback
        
    Returns:
        Text embedding service instance
    """
    if use_cloud and Config.NVIDIA_API_KEY:
        return HybridEmbeddingService(prefer_cloud=True)
    return HybridEmbeddingService(prefer_cloud=False)


def create_image_embedding_service(use_cloud: bool = True) -> Union[NVIDIAImageEmbeddingService, HybridImageEmbeddingService]:
    """
    Create image embedding service based on configuration.
    
    Args:
        use_cloud: If True, prefer cloud service with local fallback
        
    Returns:
        Image embedding service instance
    """
    if use_cloud and Config.NVIDIA_API_KEY:
        return HybridImageEmbeddingService(prefer_cloud=True)
    return HybridImageEmbeddingService(prefer_cloud=False)
