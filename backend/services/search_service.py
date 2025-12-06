# backend/services/search_service.py
"""
Semantic Search Service for Customer Portal
Provides text-based semantic search, image similarity search, and nearby shop discovery.

Supports:
- NVIDIA NIM Cloud Embeddings (preferred, more efficient)
- Local sentence-transformers (fallback)
- FAISS for vector similarity search
"""

import os
import re
import json
import hashlib
import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
from math import radians, sin, cos, sqrt, atan2

from config import Config

# Try importing NVIDIA embedding service
try:
    from services.nvidia_embedding_service import (
        HybridEmbeddingService,
        create_text_embedding_service,
        TEXT_EMBEDDING_DIM as NVIDIA_EMBEDDING_DIM
    )
    NVIDIA_EMBEDDING_AVAILABLE = True
except ImportError:
    NVIDIA_EMBEDDING_AVAILABLE = False
    NVIDIA_EMBEDDING_DIM = None
    print("[Search Service] NVIDIA embedding service not available")

# Try importing ML libraries - graceful degradation if not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[Search Service] sentence-transformers not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("[Search Service] FAISS not available, using fallback similarity search")

from models.model import db, Shop, Product, ProductImage, Inventory


# ============================================================================
# CONFIGURATION
# ============================================================================

# Embedding provider selection: 'nvidia' (cloud) or 'local'
EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'nvidia').lower()
USE_CLOUD_EMBEDDINGS = EMBEDDING_PROVIDER == 'nvidia' and Config.NVIDIA_API_KEY

# Local model settings (fallback)
LOCAL_EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
LOCAL_EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Dynamic embedding dimension based on provider
EMBEDDING_DIM = NVIDIA_EMBEDDING_DIM if USE_CLOUD_EMBEDDINGS and NVIDIA_EMBEDDING_AVAILABLE else LOCAL_EMBEDDING_DIM

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'faiss')
EARTH_RADIUS_KM = 6371.0

# Log embedding configuration
if USE_CLOUD_EMBEDDINGS and NVIDIA_EMBEDDING_AVAILABLE:
    print(f"[Search Service] Using NVIDIA Cloud Embeddings (dim={EMBEDDING_DIM})")
elif SENTENCE_TRANSFORMERS_AVAILABLE:
    print(f"[Search Service] Using Local sentence-transformers (dim={EMBEDDING_DIM})")
else:
    print("[Search Service] No embedding service available, using text search fallback")

# Cache settings
SEARCH_CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 500


# ============================================================================
# SEARCH CACHE
# ============================================================================

class SearchCache:
    """In-memory cache for search results with TTL."""
    
    def __init__(self, ttl_seconds: int = SEARCH_CACHE_TTL, max_size: int = MAX_CACHE_SIZE):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        key = self._generate_key(prefix, *args, **kwargs)
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, prefix: str, value: Any, *args, **kwargs):
        if len(self._cache) >= self.max_size:
            # Evict oldest entries
            oldest = sorted(self._cache.items(), key=lambda x: x[1][1])[:self.max_size // 4]
            for k, _ in oldest:
                del self._cache[k]
        
        key = self._generate_key(prefix, *args, **kwargs)
        self._cache[key] = (value, time.time())
    
    def clear(self):
        self._cache.clear()


# Global cache instance
search_cache = SearchCache()


# ============================================================================
# EMBEDDING SERVICE
# ============================================================================

class EmbeddingService:
    """
    Manages text embeddings with cloud-first approach.
    
    Uses NVIDIA NIM API for cloud embeddings (preferred) with local fallback.
    The cloud API provides:
    - Faster indexing (no local GPU required)
    - Higher quality embeddings (1024 dim vs 384 dim)
    - input_type differentiation for better accuracy
    """
    
    _instance = None
    _model = None
    _cloud_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None and self._cloud_service is None:
            # Try NVIDIA cloud service first
            if USE_CLOUD_EMBEDDINGS and NVIDIA_EMBEDDING_AVAILABLE:
                try:
                    print(f"[Embedding Service] Initializing NVIDIA Cloud Embeddings...")
                    self._cloud_service = create_text_embedding_service(use_cloud=True)
                    if self._cloud_service.available:
                        print(f"[Embedding Service] NVIDIA Cloud Embeddings ready (dim={self._cloud_service.embedding_dim})")
                    else:
                        self._cloud_service = None
                except Exception as e:
                    print(f"[Embedding Service] NVIDIA service init failed: {e}")
                    self._cloud_service = None
            
            # Fall back to local model if cloud not available
            if self._cloud_service is None and SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    print(f"[Embedding Service] Loading local model: {LOCAL_EMBEDDING_MODEL}")
                    self._model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
                    print(f"[Embedding Service] Local model loaded successfully")
                except Exception as e:
                    print(f"[Embedding Service] Failed to load local model: {e}")
                    self._model = None
    
    @property
    def available(self) -> bool:
        return self._cloud_service is not None or self._model is not None
    
    @property
    def is_cloud(self) -> bool:
        return self._cloud_service is not None
    
    @property
    def embedding_dim(self) -> int:
        if self._cloud_service is not None:
            return self._cloud_service.embedding_dim
        return LOCAL_EMBEDDING_DIM
    
    def encode(self, texts: List[str], show_progress: bool = False, input_type: str = "passage") -> Optional[np.ndarray]:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of texts to encode
            show_progress: Show progress bar (local model only)
            input_type: 'passage' for indexing, 'query' for searching (cloud only)
            
        Returns:
            numpy array of embeddings or None if failed
        """
        if not self.available:
            return None
        
        # Use cloud service if available
        if self._cloud_service is not None:
            try:
                return self._cloud_service.encode(texts, input_type=input_type, show_progress=show_progress)
            except Exception as e:
                print(f"[Embedding Service] Cloud encoding error: {e}")
                # Fall through to local if cloud fails
                if self._model is not None:
                    print("[Embedding Service] Falling back to local model...")
                else:
                    return None
        
        # Use local model
        try:
            embeddings = self._model.encode(texts, show_progress_bar=show_progress)
            return np.array(embeddings).astype('float32')
        except Exception as e:
            print(f"[Embedding Service] Local encoding error: {e}")
            return None
    
    def encode_single(self, text: str, input_type: str = "query") -> Optional[np.ndarray]:
        """Encode single text to embedding."""
        result = self.encode([text], input_type=input_type)
        return result[0] if result is not None else None


# Global embedding service
embedding_service = EmbeddingService()


# ============================================================================
# FAISS INDEX MANAGER
# ============================================================================

class FAISSIndexManager:
    """Manages FAISS indices for product and shop search."""
    
    def __init__(self):
        self.product_index = None
        self.product_ids = []
        self.shop_index = None
        self.shop_ids = []
        self._embedding_dim = None  # Dynamic dimension
        self._ensure_index_dir()
    
    def _ensure_index_dir(self):
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    
    def _get_product_index_path(self) -> str:
        return os.path.join(FAISS_INDEX_PATH, 'products.index')
    
    def _get_shop_index_path(self) -> str:
        return os.path.join(FAISS_INDEX_PATH, 'shops.index')
    
    def _get_current_embedding_dim(self) -> int:
        """Get embedding dimension from the current service."""
        if embedding_service.available:
            return embedding_service.embedding_dim
        return EMBEDDING_DIM
    
    def build_product_index(self, force_rebuild: bool = False) -> bool:
        """Build FAISS index for products."""
        if not FAISS_AVAILABLE or not embedding_service.available:
            print("[FAISS] Dependencies not available for product index")
            return False
        
        index_path = self._get_product_index_path()
        meta_path = index_path + '.meta.json'
        
        # Check if we need to rebuild due to dimension change
        if os.path.exists(meta_path) and not force_rebuild:
            try:
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                    stored_dim = meta.get('embedding_dim')
                    current_dim = self._get_current_embedding_dim()
                    if stored_dim and stored_dim != current_dim:
                        print(f"[FAISS] Embedding dimension changed ({stored_dim} -> {current_dim}), rebuilding...")
                        force_rebuild = True
            except Exception:
                pass
        
        if os.path.exists(index_path) and not force_rebuild:
            return self.load_product_index()
        
        try:
            products = Product.query.filter_by(is_active=True).all()
            if not products:
                print("[FAISS] No products to index")
                return False
            
            # Create text representations for products
            texts = []
            self.product_ids = []
            for p in products:
                text = f"{p.name} {p.category or ''} {p.description or ''}"
                texts.append(text)
                self.product_ids.append(p.id)
            
            # Generate embeddings (using 'passage' type for indexing)
            print(f"[FAISS] Generating embeddings for {len(texts)} products...")
            embeddings = embedding_service.encode(texts, show_progress=True, input_type="passage")
            if embeddings is None:
                return False
            
            # Get actual embedding dimension
            self._embedding_dim = embeddings.shape[1]
            print(f"[FAISS] Embedding dimension: {self._embedding_dim}")
            
            # Build FAISS index
            self.product_index = faiss.IndexFlatIP(self._embedding_dim)  # Inner product for cosine similarity
            faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
            self.product_index.add(embeddings)
            
            # Save index
            faiss.write_index(self.product_index, index_path)
            
            # Save metadata including embedding dimension
            with open(meta_path, 'w') as f:
                json.dump({
                    'product_ids': self.product_ids,
                    'embedding_dim': self._embedding_dim,
                    'is_cloud': embedding_service.is_cloud,
                    'indexed_at': time.time()
                }, f)
            
            print(f"[FAISS] Product index built with {len(products)} products (dim={self._embedding_dim})")
            return True
            
        except Exception as e:
            print(f"[FAISS] Error building product index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_product_index(self) -> bool:
        """Load existing product index."""
        if not FAISS_AVAILABLE:
            return False
        
        index_path = self._get_product_index_path()
        meta_path = index_path + '.meta.json'
        
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            return False
        
        try:
            self.product_index = faiss.read_index(index_path)
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                self.product_ids = meta.get('product_ids', [])
                self._embedding_dim = meta.get('embedding_dim', EMBEDDING_DIM)
            
            print(f"[FAISS] Product index loaded with {len(self.product_ids)} products (dim={self._embedding_dim})")
            return True
        except Exception as e:
            print(f"[FAISS] Error loading product index: {e}")
            return False
    
    def search_products(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """Search products by semantic similarity."""
        if self.product_index is None:
            if not self.load_product_index() and not self.build_product_index():
                return []
        
        if not embedding_service.available:
            return []
        
        try:
            # Use 'query' type for search queries (better accuracy with cloud)
            query_embedding = embedding_service.encode_single(query, input_type="query")
            if query_embedding is None:
                return []
            
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            scores, indices = self.product_index.search(query_embedding, top_k)
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if idx >= 0 and idx < len(self.product_ids):
                    results.append((self.product_ids[idx], float(score)))
            
            return results
            
        except Exception as e:
            print(f"[FAISS] Product search error: {e}")
            return []


# Global index manager
faiss_manager = FAISSIndexManager()


# ============================================================================
# GEO UTILITIES
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def get_bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """Calculate bounding box for geo search optimization."""
    lat_delta = radius_km / 111.0  # ~111km per degree latitude
    lon_delta = radius_km / (111.0 * cos(radians(lat)))
    
    return (
        lat - lat_delta,  # min_lat
        lat + lat_delta,  # max_lat
        lon - lon_delta,  # min_lon
        lon + lon_delta   # max_lon
    )


# ============================================================================
# SEARCH FUNCTIONS
# ============================================================================

def extract_search_filters(query: str) -> Tuple[str, Optional[float], Optional[float]]:
    """
    Extract price filters from natural language query.
    Returns: (cleaned_query, min_price, max_price)
    """
    min_price = None
    max_price = None
    clean_query = query
    
    # Patterns for price extraction
    # "under 500", "below 500", "< 500"
    under_pattern = re.search(r'(?:under|below|less than|<)\s*₹?\s*(\d+(?:,\d+)*)', query, re.IGNORECASE)
    if under_pattern:
        try:
            max_price = float(under_pattern.group(1).replace(',', ''))
            # Remove the price part from query to improve semantic search
            clean_query = re.sub(r'(?:under|below|less than|<)\s*₹?\s*(\d+(?:,\d+)*)', '', clean_query, flags=re.IGNORECASE)
        except ValueError:
            pass

    # "above 500", "over 500", "> 500"
    above_pattern = re.search(r'(?:above|over|more than|>)\s*₹?\s*(\d+(?:,\d+)*)', query, re.IGNORECASE)
    if above_pattern:
        try:
            min_price = float(above_pattern.group(1).replace(',', ''))
            clean_query = re.sub(r'(?:above|over|more than|>)\s*₹?\s*(\d+(?:,\d+)*)', '', clean_query, flags=re.IGNORECASE)
        except ValueError:
            pass
            
    # "between 500 and 1000", "500-1000"
    range_pattern = re.search(r'(?:between)?\s*₹?\s*(\d+(?:,\d+)*)\s*(?:and|-|to)\s*₹?\s*(\d+(?:,\d+)*)', query, re.IGNORECASE)
    if range_pattern:
        try:
            p1 = float(range_pattern.group(1).replace(',', ''))
            p2 = float(range_pattern.group(2).replace(',', ''))
            min_price = min(p1, p2)
            max_price = max(p1, p2)
            clean_query = re.sub(r'(?:between)?\s*₹?\s*(\d+(?:,\d+)*)\s*(?:and|-|to)\s*₹?\s*(\d+(?:,\d+)*)', '', clean_query, flags=re.IGNORECASE)
        except ValueError:
            pass

    return clean_query.strip(), min_price, max_price


def semantic_search_products(
    query: str,
    shop_id: Optional[int] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Semantic search for products with optional filters.
    Falls back to text search if embeddings unavailable.
    Returns dict with 'products' list and 'filters' dict.
    """
    # Extract filters from query if not provided
    clean_query, q_min_price, q_max_price = extract_search_filters(query)
    
    # Use extracted filters if explicit ones are not provided
    if min_price is None: min_price = q_min_price
    if max_price is None: max_price = q_max_price
    
    # Use cleaned query for semantic search (better results without numbers)
    search_query = clean_query if clean_query else query

    # Check cache
    cache_key = (search_query, shop_id, category, min_price, max_price, limit)
    cached = search_cache.get('semantic_products', *cache_key)
    if cached:
        return cached
    
    results = []
    
    # Try semantic search first
    if embedding_service.available and FAISS_AVAILABLE:
        # Fetch more candidates to allow for filtering
        candidate_limit = limit * 5
        semantic_results = faiss_manager.search_products(search_query, top_k=candidate_limit)
        
        if semantic_results:
            product_ids = [pid for pid, _ in semantic_results]
            score_map = {pid: score for pid, score in semantic_results}
            
            # Fetch products with filters
            query_obj = Product.query.filter(
                Product.id.in_(product_ids),
                Product.is_active == True
            )
            
            if shop_id:
                query_obj = query_obj.filter(Product.shop_id == shop_id)
            if category:
                query_obj = query_obj.filter(Product.category.ilike(f'%{category}%'))
            if min_price is not None:
                query_obj = query_obj.filter(Product.price >= min_price)
            if max_price is not None:
                query_obj = query_obj.filter(Product.price <= max_price)
            
            products = query_obj.all()
            
            # Calculate combined scores with text match boosting
            search_lower = search_query.lower()
            search_terms = set(search_lower.split())
            
            def calculate_boosted_score(product, base_score):
                """Boost score based on text match quality."""
                name_lower = (product.name or '').lower()
                category_lower = (product.category or '').lower()
                
                boost = 0.0
                
                # Exact name match - massive boost
                if search_lower == name_lower:
                    boost += 0.5
                # Name contains full query
                elif search_lower in name_lower:
                    boost += 0.35
                # Query contains product name
                elif name_lower in search_lower:
                    boost += 0.3
                else:
                    # Count matching words
                    name_words = set(name_lower.split())
                    matching_words = search_terms & name_words
                    if matching_words:
                        word_match_ratio = len(matching_words) / max(len(search_terms), len(name_words))
                        boost += 0.25 * word_match_ratio
                
                # Category match boost
                if category_lower and any(term in category_lower for term in search_terms):
                    boost += 0.1
                
                # Combine: base semantic score + text match boost, cap at 1.0
                return min(base_score + boost, 1.0)
            
            # Calculate boosted scores and sort
    # Filter by 50% accuracy threshold
    products_with_scores = [
        (p, calculate_boosted_score(p, score_map.get(p.id, 0)))
        for p in products
    ]
    
    # Sort by score
    products_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    for product, boosted_score in products_with_scores[:limit]:
        relevance = round(boosted_score * 100, 2)
        if relevance >= 50.0:  # Strict 50% threshold
            results.append({
                **product.to_card_dict(),
                'relevance_score': relevance,
                'shop': product.shop.to_card_dict() if product.shop else None
            })

    # Fallback to text search
    if not results:
        results = fallback_text_search_products(
            query, shop_id, category, min_price, max_price, limit
        )
        # Ensure fallback results also meet threshold
        results = [r for r in results if r.get('relevance_score', 0) >= 50.0]

    response = {
        'products': results,
        'filters': {
            'min_price': min_price,
            'max_price': max_price,
            'extracted_query': clean_query
        }
    }
    
    search_cache.set('semantic_products', response, *cache_key)
    return response


def fallback_text_search_products(
    query: str,
    shop_id: Optional[int] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Text-based product search fallback using SQL LIKE with relevance scoring."""
    search_terms = query.lower().split()
    search_lower = query.lower()
    
    query_obj = Product.query.filter(Product.is_active == True)
    
    # Build OR conditions for each search term
    from sqlalchemy import or_
    for term in search_terms[:5]:  # Limit terms
        pattern = f'%{term}%'
        query_obj = query_obj.filter(
            or_(
                Product.name.ilike(pattern),
                Product.category.ilike(pattern),
                Product.description.ilike(pattern)
            )
        )
    
    if shop_id:
        query_obj = query_obj.filter(Product.shop_id == shop_id)
    if category:
        query_obj = query_obj.filter(Product.category.ilike(f'%{category}%'))
    if min_price is not None:
        query_obj = query_obj.filter(Product.price >= min_price)
    if max_price is not None:
        query_obj = query_obj.filter(Product.price <= max_price)
    
    products = query_obj.order_by(Product.rating.desc()).limit(limit * 2).all()
    
    # Calculate relevance scores based on text matching
    def calc_text_relevance(product):
        name_lower = (product.name or '').lower()
        category_lower = (product.category or '').lower()
        desc_lower = (product.description or '').lower()
        
        score = 0.5  # Base score for matching products
        
        # Exact name match
        if search_lower == name_lower:
            score = 1.0
        # Name contains full query
        elif search_lower in name_lower:
            score = 0.95
        # Query contains product name  
        elif name_lower in search_lower:
            score = 0.90
        else:
            # Count matching words in name
            name_words = set(name_lower.split())
            search_set = set(search_terms)
            matching = name_words & search_set
            if matching:
                score = 0.5 + (0.35 * len(matching) / max(len(search_set), len(name_words)))
        
        # Category bonus
        if category_lower and any(term in category_lower for term in search_terms):
            score = min(score + 0.05, 1.0)
        
        return score
    
    # Score and sort products
    scored_products = [(p, calc_text_relevance(p)) for p in products]
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    return [
        {
            **p.to_card_dict(),
            'relevance_score': round(score * 100, 2),
            'shop': p.shop.to_card_dict() if p.shop else None
        }
        for p, score in scored_products[:limit]
    ]


def search_shops(
    query: Optional[str] = None,
    city: Optional[str] = None,
    has_product_category: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search shops with optional filters."""
    cache_key = (query, city, has_product_category, min_rating, limit)
    cached = search_cache.get('search_shops', *cache_key)
    if cached:
        return cached
    
    from sqlalchemy import or_, distinct
    
    query_obj = Shop.query
    
    if query:
        pattern = f'%{query}%'
        query_obj = query_obj.filter(
            or_(
                Shop.name.ilike(pattern),
                Shop.description.ilike(pattern),
                Shop.city.ilike(pattern),
                Shop.address.ilike(pattern)
            )
        )
    
    if city:
        query_obj = query_obj.filter(Shop.city.ilike(f'%{city}%'))
    
    if min_rating:
        query_obj = query_obj.filter(Shop.rating >= min_rating)
    
    if has_product_category:
        # Join with products to filter by category
        query_obj = query_obj.join(Product).filter(
            Product.category.ilike(f'%{has_product_category}%'),
            Product.is_active == True
        ).distinct()
    
    shops = query_obj.order_by(Shop.rating.desc(), Shop.is_popular.desc()).limit(limit).all()
    
    results = []
    for shop in shops:
        shop_dict = shop.to_detail_dict()
        
        # Add product categories available at this shop
        categories = db.session.query(distinct(Product.category)).filter(
            Product.shop_id == shop.id,
            Product.is_active == True,
            Product.category.isnot(None)
        ).limit(10).all()
        shop_dict['categories'] = [c[0] for c in categories if c[0]]
        
        results.append(shop_dict)
    
    search_cache.set('search_shops', results, *cache_key)
    return results


def find_nearby_shops(
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    product_query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Find shops within radius of given coordinates.
    Optionally filter by product availability.
    """
    cache_key = (round(lat, 4), round(lon, 4), radius_km, product_query, category, limit)
    cached = search_cache.get('nearby_shops', *cache_key)
    if cached:
        return cached
    
    # Get bounding box for initial filtering
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_km)
    
    # Query shops within bounding box
    query_obj = Shop.query.filter(
        Shop.lat.isnot(None),
        Shop.lon.isnot(None),
        Shop.lat.between(min_lat, max_lat),
        Shop.lon.between(min_lon, max_lon)
    )
    
    # Filter by product category if specified
    if category:
        query_obj = query_obj.join(Product).filter(
            Product.category.ilike(f'%{category}%'),
            Product.is_active == True
        ).distinct()
    
    shops = query_obj.all()
    
    # Calculate exact distances and filter
    results = []
    for shop in shops:
        distance = haversine_distance(lat, lon, shop.lat, shop.lon)
        if distance <= radius_km:
            shop_dict = shop.to_detail_dict()
            shop_dict['distance_km'] = round(distance, 2)
            shop_dict['distance_text'] = f"{distance:.1f} km" if distance >= 1 else f"{int(distance * 1000)} m"
            
            # If product query specified, check for matching products
            if product_query:
                matching_products = semantic_search_products(
                    product_query, 
                    shop_id=shop.id, 
                    category=category,
                    limit=5
                )
                shop_dict['matching_products'] = matching_products
                shop_dict['has_matching_products'] = len(matching_products) > 0
            
            results.append(shop_dict)
    
    # Sort by distance
    results.sort(key=lambda x: x['distance_km'])
    results = results[:limit]
    
    search_cache.set('nearby_shops', results, *cache_key)
    return results


def get_search_suggestions(
    query: str,
    limit: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get search suggestions for autocomplete.
    Returns both product and shop suggestions.
    """
    if len(query) < 2:
        return {'products': [], 'shops': [], 'categories': []}
    
    cache_key = (query.lower(), limit)
    cached = search_cache.get('suggestions', *cache_key)
    if cached:
        return cached
    
    pattern = f'{query}%'
    
    # Product suggestions
    products = Product.query.filter(
        Product.is_active == True,
        Product.name.ilike(pattern)
    ).order_by(Product.rating.desc()).limit(limit).all()
    
    product_suggestions = [
        {'id': p.id, 'name': p.name, 'type': 'product', 'category': p.category}
        for p in products
    ]
    
    # Shop suggestions
    shops = Shop.query.filter(
        Shop.name.ilike(pattern)
    ).order_by(Shop.rating.desc()).limit(limit).all()
    
    shop_suggestions = [
        {'id': s.id, 'name': s.name, 'type': 'shop', 'city': s.city}
        for s in shops
    ]
    
    # Category suggestions
    from sqlalchemy import distinct
    categories = db.session.query(distinct(Product.category)).filter(
        Product.category.ilike(pattern),
        Product.is_active == True
    ).limit(limit).all()
    
    category_suggestions = [
        {'name': c[0], 'type': 'category'}
        for c in categories if c[0]
    ]
    
    result = {
        'products': product_suggestions,
        'shops': shop_suggestions,
        'categories': category_suggestions
    }
    
    search_cache.set('suggestions', result, *cache_key)
    return result


# ============================================================================
# INDEX MANAGEMENT
# ============================================================================

def rebuild_search_indices():
    """Rebuild all search indices."""
    search_cache.clear()
    faiss_manager.build_product_index(force_rebuild=True)
    return {'status': 'success', 'message': 'Search indices rebuilt'}


def get_search_service_status() -> Dict[str, Any]:
    """Get status of search service components."""
    return {
        'embedding_service': {
            'available': embedding_service.available,
            'is_cloud': embedding_service.is_cloud if embedding_service.available else False,
            'provider': 'nvidia_cloud' if embedding_service.is_cloud else 'local',
            'model': 'nv-embedqa-e5-v5' if embedding_service.is_cloud else LOCAL_EMBEDDING_MODEL,
            'embedding_dim': embedding_service.embedding_dim if embedding_service.available else None
        },
        'faiss': {
            'available': FAISS_AVAILABLE,
            'product_index_loaded': faiss_manager.product_index is not None,
            'indexed_products': len(faiss_manager.product_ids) if faiss_manager.product_ids else 0,
            'index_embedding_dim': faiss_manager._embedding_dim
        },
        'cache': {
            'entries': len(search_cache._cache),
            'ttl_seconds': search_cache.ttl
        },
        'config': {
            'use_cloud_embeddings': USE_CLOUD_EMBEDDINGS,
            'embedding_provider': EMBEDDING_PROVIDER
        }
    }
