"""
Performance optimization utilities for SE-Textile Backend
"""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Optional, Dict
from services.ai_service import generate_ai_caption, DEFAULT_CAPTION

# Simple in-memory cache (for production, use Redis)
_cache: Dict[str, Dict[str, Any]] = {}

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a consistent cache key."""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    if key in _cache:
        cache_entry = _cache[key]
        if time.time() - cache_entry['timestamp'] < cache_entry['ttl']:
            return cache_entry['value']
        else:
            # Remove expired entry
            del _cache[key]
    return None

def cache_set(key: str, value: Any, ttl: int = 86400) -> None:
    """Set value in cache with TTL."""
    _cache[key] = {
        'value': value,
        'timestamp': time.time(),
        'ttl': ttl
    }

def cached_ai_caption(product_name: str, category: str, price: float) -> str:
    """Generate AI caption with caching."""
    cache_key = get_cache_key('ai_caption', product_name, category, price)
    
    # Try to get from cache first
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Generate new caption
    try:
        caption = generate_ai_caption(product_name, category, price)
    except Exception as e:
        print(f"AI caption generation failed for {product_name}: {e}")
        caption = DEFAULT_CAPTION
    
    # Cache the result
    cache_set(cache_key, caption)
    
    return caption

def performance_monitor(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time > 2.0:  # Log operations taking more than 2 seconds
                print(f"[PERF] Slow operation detected: {func.__name__} took {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[PERF] Failed operation: {func.__name__} failed after {execution_time:.2f}s - {e}")
            raise
    return wrapper

def batch_ai_captions(products: list, generate_captions: bool = False) -> list:
    """Generate AI captions for multiple products efficiently."""
    if not generate_captions:
        return [None] * len(products)
    
    captions = []
    for product in products:
        caption = None
        try:
            caption = cached_ai_caption(
                product.name, 
                product.category or "Product", 
                float(product.price)
            )
        except Exception as e:
            print(f"AI caption failed for product {product.id}: {e}")
            caption = DEFAULT_CAPTION
        
        captions.append(caption)
    
    return captions

# Cache statistics
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring."""
    total_entries = len(_cache)
    expired_entries = sum(1 for entry in _cache.values() 
                         if time.time() - entry['timestamp'] > entry['ttl'])
    active_entries = total_entries - expired_entries
    
    return {
        'total_entries': total_entries,
        'expired_entries': expired_entries,
        'active_entries': active_entries,
        'memory_usage_estimate': total_entries * 100  # Rough estimate in bytes
    }

def clear_cache() -> None:
    """Clear all cache entries."""
    global _cache
    _cache.clear()
