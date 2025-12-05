"""
Product Image Search Service
Searches real shop products by image similarity.

This service:
1. Builds embeddings from actual ProductImage records in the database
2. Stores embeddings in a numpy file for fast loading
3. Provides search functionality for customer image uploads
"""

import os
import json
import time
import math
import numpy as np
from PIL import Image
from typing import Dict, Optional, Any

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from config import Config
from models.model import Product, ProductImage, db
from utils.image_utils import get_image_url
from services.nvidia_embedding_service import create_image_embedding_service

# Paths
EMBEDDINGS_DIR = os.path.join(Config.BASE_DIR, "instance", "embeddings")
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "product_embeddings.npz")
METADATA_FILE = os.path.join(EMBEDDINGS_DIR, "product_metadata.json")

os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

# Feature extraction settings
# NVIDIA NVCLIP uses 1024 dimensions
EMBEDDING_DIM = 1024 


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    try:
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return float('inf')


class ProductImageSearchService:
    """Service for searching products by image similarity."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.embeddings = None  # np.ndarray (N, EMBEDDING_DIM)
        self.product_ids = []   # List of product IDs
        self.image_ids = []     # List of ProductImage IDs  
        self.image_urls = []    # List of image URLs
        self.index = None       # FAISS index
        
        # Initialize NVIDIA/Hybrid Embedding Service
        self.embedding_service = create_image_embedding_service(use_cloud=True)
        
        self._initialized = True
        
        # Try to load existing embeddings
        self._load_embeddings()
    
    def _extract_features(self, image: Image.Image) -> np.ndarray:
        """
        Extract feature vector from PIL Image using NVIDIA/Hybrid service.
        """
        embedding = self.embedding_service.encode_image(image)
        if embedding is None:
            # Fallback to zero vector if extraction fails
            return np.zeros(EMBEDDING_DIM, dtype=np.float32)
        return embedding
    
    def _extract_features_from_bytes(self, img_bytes: bytes) -> Optional[np.ndarray]:
        """Extract features from image bytes."""
        return self.embedding_service.encode_image_bytes(img_bytes)
    
    def _extract_features_from_url(self, url: str) -> Optional[np.ndarray]:
        """Extract features from image URL."""
        # Handle local file paths (e.g., 'uploads/product_images/...')
        if not url.startswith(('http://', 'https://')):
            # Remove leading slash if present
            clean_path = url.lstrip('/')
            
            # Construct absolute path
            local_path = os.path.join(Config.BASE_DIR, clean_path)
            
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as f:
                        return self.embedding_service.encode_image_bytes(f.read())
                except Exception as e:
                    print(f"[ProductImageSearch] Failed to read local file {local_path}: {e}")
                    return None
            else:
                print(f"[ProductImageSearch] Local file not found: {local_path}")
                return None

        # Handle actual URLs
        return self.embedding_service.encode_image_url(url)
    
    def _load_embeddings(self) -> bool:
        """Load embeddings from file."""
        if not os.path.exists(EMBEDDINGS_FILE) or not os.path.exists(METADATA_FILE):
            print("[ProductImageSearch] No embeddings found, will build on first search")
            return False
        
        try:
            # Load embeddings
            data = np.load(EMBEDDINGS_FILE)
            loaded_embeddings = data['embeddings']
            
            # Check dimension compatibility
            if loaded_embeddings.shape[1] != EMBEDDING_DIM:
                print(f"[ProductImageSearch] Dimension mismatch (File: {loaded_embeddings.shape[1]}, Model: {EMBEDDING_DIM}). Rebuilding index...")
                return False

            self.embeddings = loaded_embeddings
            
            # Load metadata
            with open(METADATA_FILE, 'r') as f:
                meta = json.load(f)
            
            self.product_ids = meta.get('product_ids', [])
            self.image_ids = meta.get('image_ids', [])
            self.image_urls = meta.get('image_urls', [])
            
            # Build FAISS index if available
            if FAISS_AVAILABLE and self.embeddings is not None:
                try:
                    print(f"[ProductImageSearch] Building FAISS index for {len(self.embeddings)} images...")
                    self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
                    # Ensure embeddings are normalized for cosine similarity
                    # Note: self.embeddings is already a numpy array, but we need to make sure it's float32
                    if self.embeddings.dtype != np.float32:
                        self.embeddings = self.embeddings.astype(np.float32)
                    
                    # Normalize in place if possible, or copy
                    faiss.normalize_L2(self.embeddings)
                    self.index.add(self.embeddings)
                    print("[ProductImageSearch] FAISS index built successfully")
                except Exception as e:
                    print(f"[ProductImageSearch] Failed to build FAISS index: {e}")
                    self.index = None
            
            print(f"[ProductImageSearch] Loaded {len(self.product_ids)} product embeddings")
            return True
        except Exception as e:
            print(f"[ProductImageSearch] Failed to load embeddings: {e}")
            return False
    
    def build_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build search index from database images.
        """
        if not force_rebuild and self.embeddings is not None:
            return {'success': True, 'message': 'Index already exists'}
            
        print("[ProductImageSearch] Building index from database...")
        start_time = time.time()
        
        result = {
            'success': False,
            'images_processed': 0,
            'products_processed': 0,
            'errors': []
        }
        
        try:
            # Fetch all product images
            # Join with Product to ensure product is active
            images = db.session.query(ProductImage).join(Product).filter(
                Product.is_active == True
            ).all()
            
            if not images:
                result['message'] = 'No product images found in database'
                return result
            
            new_embeddings = []
            new_product_ids = []
            new_image_ids = []
            new_image_urls = []
            
            processed_count = 0
            
            for img in images:
                try:
                    # Get image URL - handle both 'url' and 'image_url' attributes
                    image_url = getattr(img, 'url', None) or getattr(img, 'image_url', None)
                    
                    if not image_url:
                        continue
                        
                    # Extract features
                    features = self._extract_features_from_url(image_url)
                    
                    if features is not None:
                        new_embeddings.append(features)
                        new_product_ids.append(img.product_id)
                        new_image_ids.append(img.id)
                        new_image_urls.append(image_url)
                        processed_count += 1
                        
                        if processed_count % 10 == 0:
                            print(f"[ProductImageSearch] Processed {processed_count} images...")
                            
                except Exception as e:
                    print(f"[ProductImageSearch] Error processing image {img.id}: {e}")
            
            if new_embeddings:
                # Convert to numpy array
                self.embeddings = np.array(new_embeddings, dtype=np.float32)
                self.product_ids = new_product_ids
                self.image_ids = new_image_ids
                self.image_urls = new_image_urls
                
                # Save to disk
                np.savez_compressed(EMBEDDINGS_FILE, embeddings=self.embeddings)
                
                with open(METADATA_FILE, 'w') as f:
                    json.dump({
                        'product_ids': self.product_ids,
                        'image_ids': self.image_ids,
                        'image_urls': self.image_urls
                    }, f)
                
                # Rebuild FAISS index
                if FAISS_AVAILABLE:
                    try:
                        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
                        # Normalize in place if possible
                        if self.embeddings.dtype != np.float32:
                            self.embeddings = self.embeddings.astype(np.float32)
                        faiss.normalize_L2(self.embeddings)
                        self.index.add(self.embeddings)
                    except Exception as e:
                        print(f"[ProductImageSearch] Failed to rebuild FAISS index: {e}")
                        self.index = None

                result['success'] = True
                result['products_processed'] = len(set(new_product_ids))
                result['images_processed'] = len(new_image_ids)
                result['message'] = f"Built index with {result['images_processed']} images from {result['products_processed']} products"
            else:
                result['message'] = 'No valid embeddings generated'
            
        except Exception as e:
            result['errors'].append(str(e))
            print(f"[ProductImageSearch] Build error: {e}")
        
        return result
    
    def search(
        self,
        image_file,
        limit: int = 20,
        min_similarity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Search for similar products by uploaded image.
        
        Args:
            image_file: File-like object with image data
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            Dict with similar_products list and metadata
        """
        result = {
            'similar_products': [],
            'total_indexed': 0,
            'search_time_ms': 0
        }
        
        start_time = time.time()
        
        # Ensure index exists
        if self.embeddings is None or len(self.product_ids) == 0:
            build_result = self.build_index()
            if not build_result['success']:
                result['error'] = 'Failed to build search index'
                return result
        
        result['total_indexed'] = len(self.product_ids)
        
        # Extract features from query image
        try:
            image_file.seek(0)
            query_features = self._extract_features_from_bytes(image_file.read())
            if query_features is None:
                result['error'] = 'Failed to process uploaded image'
                return result
        except Exception as e:
            result['error'] = f'Image processing error: {str(e)}'
            return result
        
        # Use FAISS if available
        if self.index is not None:
            # Normalize query
            query_features = query_features.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_features)
            
            # Search
            # Fetch more to handle duplicate products
            k = limit * 3
            similarities, indices = self.index.search(query_features, k)
            
            top_indices = indices[0]
            similarities = similarities[0]
        else:
            # Fallback to numpy
            similarities = self.embeddings @ query_features
            top_indices = np.argsort(similarities)[::-1]
        
        # Collect unique products
        seen_products = set()
        matches = []
        
        for i, idx in enumerate(top_indices):
            if idx < 0 or idx >= len(self.product_ids):
                continue
                
            if len(matches) >= limit:
                break
            
            # Handle FAISS vs Numpy similarity access
            if self.index is not None:
                similarity = float(similarities[i])
            else:
                similarity = float(similarities[idx])
                
            if similarity < min_similarity:
                continue
            
            product_id = self.product_ids[idx]
            if product_id in seen_products:
                continue
            
            seen_products.add(product_id)
            matches.append({
                'product_id': product_id,
                'image_id': self.image_ids[idx],
                'image_url': self.image_urls[idx],
                'similarity': round(similarity * 100, 2)  # Convert to percentage
            })
        
        # Enrich with product details
        if matches:
            product_ids = [m['product_id'] for m in matches]
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            product_map = {p.id: p for p in products}
            
            for match in matches:
                product = product_map.get(match['product_id'])
                if product:
                    # Resolve image URL to full path for frontend
                    resolved_image = get_image_url(match['image_url'], product.id, "product")
                    
                    item = {
                        'id': product.id,
                        'name': product.name,
                        'category': product.category,
                        'price': float(product.price) if product.price else 0,
                        'price_formatted': f"₹{product.price:,.0f}" if product.price else "₹0",
                        'rating': round(product.rating or 4.0, 1),
                        'image': resolved_image,
                        'matched_image': resolved_image,
                        'similarity_score': match['similarity'],
                        'shop': product.shop.to_card_dict() if product.shop else None
                    }
                    
                    result['similar_products'].append(item)
        
        result['search_time_ms'] = round((time.time() - start_time) * 1000, 2)
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'available': True,
            'index_loaded': self.embeddings is not None,
            'total_images': len(self.image_ids) if self.image_ids else 0,
            'total_products': len(set(self.product_ids)) if self.product_ids else 0,
            'embedding_dim': EMBEDDING_DIM,
            'embeddings_file': EMBEDDINGS_FILE if os.path.exists(EMBEDDINGS_FILE) else None
        }


# Global service instance
product_image_search = ProductImageSearchService()


# Public API functions
def search_products_by_image(image_file, limit: int = 20, min_similarity: float = 0.85) -> Dict[str, Any]:
    """Search for similar products by image with at least 75% similarity."""
    return product_image_search.search(image_file, limit=limit, min_similarity=min_similarity)


def rebuild_product_image_index() -> Dict[str, Any]:
    """Rebuild the product image search index."""
    return product_image_search.build_index(force_rebuild=True)


def get_image_search_status() -> Dict[str, Any]:
    """Get image search service status."""
    return product_image_search.get_status()


def init_product_image_search():
    """Initialize product image search on app startup."""
    print("[ProductImageSearch] Initializing...")
    status = product_image_search.get_status()
    if not status['index_loaded']:
        print("[ProductImageSearch] Building index...")
        result = product_image_search.build_index()
        print(f"[ProductImageSearch] {result.get('message', 'Done')}")
    else:
        print(f"[ProductImageSearch] Index ready with {status['total_images']} images")
