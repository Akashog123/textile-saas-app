# backend/utils/image_utils.py
"""
Image URL utilities for production-ready image serving
"""

from config import Config


def get_image_url(image_path, fallback_id=None, fallback_type="product"):
    """
    Generate production-ready image URL from database path.
    
    Args:
        image_path: Image path from database (e.g., "/uploads/image.jpg", "http://...")
        fallback_id: ID for placeholder image if path is None
        fallback_type: Type of placeholder ("product", "shop", "user")
    
    Returns:
        str: Absolute image URL or placeholder
    """
    if not image_path:
        if Config.USE_PLACEHOLDER_IMAGES and fallback_id:
            # Use placeholder service with deterministic seed
            dimensions = "600x400" if fallback_type == "shop" else "400x300"
            return f"{Config.PLACEHOLDER_IMAGE_SERVICE}/{dimensions}?text={fallback_type}&seed={fallback_id}"
        return ""
    
    # If already absolute URL, return as-is
    if image_path.startswith(("http://", "https://")):
        return image_path
    
    # If relative path, prepend API base URL
    if image_path.startswith("/"):
        return f"{Config.API_BASE_URL}{image_path}"
    
    # If no leading slash, assume uploads path
    return f"{Config.API_BASE_URL}{Config.STATIC_IMAGE_PATH}/{image_path}"


def resolve_product_image(product, fallback=True):
    """
    Resolve product image URL with fallback logic.
    
    Args:
        product: Product model instance
        fallback: Whether to use placeholder if no image
    
    Returns:
        str: Image URL
    """
    # Try product's direct image_url
    if hasattr(product, 'image_url') and product.image_url:
        return get_image_url(product.image_url, product.id, "product")
    
    # Try first image from images relationship
    if hasattr(product, 'images'):
        try:
            images_rel = product.images
            first_image = images_rel.first() if hasattr(images_rel, 'first') else (images_rel[0] if images_rel else None)
            if first_image and hasattr(first_image, 'url') and first_image.url:
                return get_image_url(first_image.url, product.id, "product")
        except (AttributeError, IndexError):
            pass
    
    # Try shop's image as fallback
    if hasattr(product, 'shop') and product.shop and hasattr(product.shop, 'image_url'):
        if product.shop.image_url:
            return get_image_url(product.shop.image_url, product.shop.id, "shop")
    
    # Final fallback
    if fallback:
        return get_image_url(None, getattr(product, 'id', None), "product")
    
    return ""


def resolve_shop_image(shop, fallback=True):
    """
    Resolve shop image URL with fallback logic.
    
    Args:
        shop: Shop model instance
        fallback: Whether to use placeholder if no image
    
    Returns:
        str: Image URL
    """
    # Try shop's direct image_url field
    if hasattr(shop, 'image_url') and shop.image_url:
        return get_image_url(shop.image_url, shop.id, "shop")
    
    # Try first image from images relationship (ShopImage table)
    if hasattr(shop, 'images'):
        try:
            images_rel = shop.images
            # Handle dynamic relationship - use first() for lazy queries
            first_image = images_rel.first() if hasattr(images_rel, 'first') else (images_rel[0] if images_rel else None)
            if first_image and hasattr(first_image, 'url') and first_image.url:
                return get_image_url(first_image.url, shop.id, "shop")
        except (AttributeError, IndexError):
            pass
    
    # Final fallback to placeholder
    if fallback:
        return get_image_url(None, getattr(shop, 'id', None), "shop")
    
    return ""


__all__ = [
    'get_image_url',
    'resolve_product_image',
    'resolve_shop_image'
]
