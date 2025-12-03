"""
Product Image Search Service
Searches real shop products by image similarity.

This service:
1. Builds embeddings from actual ProductImage records in the database
2. Stores embeddings in a numpy file for fast loading
3. Provides search functionality for customer image uploads
"""

import os
import io
import json
import time
import numpy as np
import requests
from PIL import Image
from typing import Dict, List, Optional, Any, Tuple
from flask import current_app

from config import Config
from models.model import db, Product, ProductImage, Shop
from utils.image_utils import get_image_url

# Paths
EMBEDDINGS_DIR = os.path.join(Config.BASE_DIR, "instance", "embeddings")
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "product_embeddings.npz")
METADATA_FILE = os.path.join(EMBEDDINGS_DIR, "product_metadata.json")

os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

# Feature extraction settings
IMAGE_SIZE = (64, 64)  # Resize to this for feature extraction
EMBEDDING_DIM = IMAGE_SIZE[0] * IMAGE_SIZE[1] * 3  # 12288 for 64x64 RGB


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
        self._initialized = True
        
        # Try to load existing embeddings
        self._load_embeddings()
    
    def _extract_features(self, image: Image.Image) -> np.ndarray:
        """
        Extract feature vector from PIL Image.
        Uses color histogram features for lightweight processing.
        """
        # Convert to RGB and resize
        image = image.convert("RGB").resize(IMAGE_SIZE)
        
        # Method 1: Flattened pixel values (simple but effective)
        pixels = np.array(image, dtype=np.float32).flatten()
        
        # Normalize to [0, 1]
        pixels = pixels / 255.0
        
        # L2 normalize for cosine similarity
        norm = np.linalg.norm(pixels)
        if norm > 0:
            pixels = pixels / norm
        
        return pixels.astype(np.float32)
    
    def _extract_features_from_bytes(self, img_bytes: bytes) -> Optional[np.ndarray]:
        """Extract features from image bytes."""
        try:
            image = Image.open(io.BytesIO(img_bytes))
            return self._extract_features(image)
        except Exception as e:
            print(f"[ProductImageSearch] Failed to extract features: {e}")
            return None
    
    def _extract_features_from_url(self, url: str) -> Optional[np.ndarray]:
        """Extract features from image URL."""
        try:
            # Handle local URLs
            if url.startswith('/uploads/') or url.startswith('uploads/'):
                local_path = os.path.join(Config.BASE_DIR, url.lstrip('/'))
                if os.path.exists(local_path):
                    with open(local_path, 'rb') as f:
                        return self._extract_features_from_bytes(f.read())
            
            # Handle full URLs
            if url.startswith('http'):
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return self._extract_features_from_bytes(response.content)
            
            # Try as local path
            if os.path.exists(url):
                with open(url, 'rb') as f:
                    return self._extract_features_from_bytes(f.read())
            
            return None
        except Exception as e:
            print(f"[ProductImageSearch] Failed to fetch image from {url}: {e}")
            return None
    
    def _load_embeddings(self) -> bool:
        """Load embeddings from file."""
        if not os.path.exists(EMBEDDINGS_FILE) or not os.path.exists(METADATA_FILE):
            print("[ProductImageSearch] No embeddings found, will build on first search")
            return False
        
        try:
            # Load embeddings
            data = np.load(EMBEDDINGS_FILE)
            self.embeddings = data['embeddings']
            
            # Load metadata
            with open(METADATA_FILE, 'r') as f:
                meta = json.load(f)
            
            self.product_ids = meta.get('product_ids', [])
            self.image_ids = meta.get('image_ids', [])
            self.image_urls = meta.get('image_urls', [])
            
            print(f"[ProductImageSearch] Loaded {len(self.product_ids)} product embeddings")
            return True
        except Exception as e:
            print(f"[ProductImageSearch] Failed to load embeddings: {e}")
            return False
    
    def _save_embeddings(self):
        """Save embeddings to file."""
        try:
            np.savez_compressed(EMBEDDINGS_FILE, embeddings=self.embeddings)
            
            meta = {
                'product_ids': self.product_ids,
                'image_ids': self.image_ids,
                'image_urls': self.image_urls,
                'embedding_dim': EMBEDDING_DIM,
                'updated_at': time.time()
            }
            with open(METADATA_FILE, 'w') as f:
                json.dump(meta, f)
            
            print(f"[ProductImageSearch] Saved {len(self.product_ids)} embeddings")
        except Exception as e:
            print(f"[ProductImageSearch] Failed to save embeddings: {e}")
    
    def build_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build embeddings index from ProductImage records.
        
        Returns:
            Dict with build status and statistics
        """
        result = {
            'success': False,
            'products_processed': 0,
            'images_processed': 0,
            'errors': []
        }
        
        # Check if rebuild needed
        if not force_rebuild and self.embeddings is not None and len(self.product_ids) > 0:
            result['success'] = True
            result['message'] = 'Index already exists'
            result['products_processed'] = len(set(self.product_ids))
            result['images_processed'] = len(self.image_ids)
            return result
        
        try:
            # Get all product images for active products
            product_images = ProductImage.query.join(Product).filter(
                Product.is_active == True
            ).order_by(ProductImage.product_id, ProductImage.ordering).all()
            
            if not product_images:
                result['message'] = 'No product images found'
                return result
            
            print(f"[ProductImageSearch] Processing {len(product_images)} images...")
            
            embeddings_list = []
            self.product_ids = []
            self.image_ids = []
            self.image_urls = []
            
            for i, img in enumerate(product_images):
                if not img.url:
                    continue
                
                # Extract features
                features = self._extract_features_from_url(img.url)
                if features is not None:
                    embeddings_list.append(features)
                    self.product_ids.append(img.product_id)
                    self.image_ids.append(img.id)
                    self.image_urls.append(img.url)
                else:
                    result['errors'].append(f"Failed to process image {img.id}")
                
                # Progress
                if (i + 1) % 10 == 0:
                    print(f"[ProductImageSearch] Processed {i + 1}/{len(product_images)}")
            
            if embeddings_list:
                self.embeddings = np.vstack(embeddings_list).astype(np.float32)
                self._save_embeddings()
                
                result['success'] = True
                result['products_processed'] = len(set(self.product_ids))
                result['images_processed'] = len(self.image_ids)
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
        
        # Compute similarities (dot product of normalized vectors = cosine similarity)
        similarities = self.embeddings @ query_features
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1]
        
        # Collect unique products
        seen_products = set()
        matches = []
        
        for idx in top_indices:
            if len(matches) >= limit:
                break
            
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
                    result['similar_products'].append({
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
                    })
        
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
def search_products_by_image(image_file, limit: int = 20) -> Dict[str, Any]:
    """Search for similar products by image."""
    return product_image_search.search(image_file, limit=limit)


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
