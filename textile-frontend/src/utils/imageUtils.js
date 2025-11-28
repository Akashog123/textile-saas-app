/**
 * Robust image handling utilities for consistent frontend parsing
 * Handles various backend image field naming conventions
 */

/**
 * Extract image URLs from product data with robust fallback handling
 * @param {Object} product - Product object from backend API
 * @param {string} fallbackText - Text to use for placeholder images
 * @returns {Array} - Array of image URLs
 */
export const getImageUrls = (product, fallbackText = 'Product') => {
  // Handle array format (most complete)
  if (product.imageUrls && Array.isArray(product.imageUrls)) {
    return product.imageUrls.filter(url => url && typeof url === 'string');
  }
  
  // Handle single image_url string
  if (product.image_url && typeof product.image_url === 'string') {
    return [product.image_url];
  }
  
  // Handle single image string (most common backend format)
  if (product.image && typeof product.image === 'string') {
    return [product.image];
  }
  
  // Handle images array from ProductImage relationship
  if (product.images && Array.isArray(product.images)) {
    const validUrls = product.images
      .map(img => img.url || img)
      .filter(url => url && typeof url === 'string');
    if (validUrls.length > 0) {
      return validUrls;
    }
  }
  
  // Fallback to placeholder
  return [`https://placehold.co/800x600?text=${encodeURIComponent(fallbackText)}`];
};

/**
 * Get primary image URL (first valid image)
 * @param {Object} product - Product object from backend API
 * @param {string} fallbackText - Text to use for placeholder image
 * @returns {string} - Primary image URL
 */
export const getPrimaryImage = (product, fallbackText = 'Product') => {
  const urls = getImageUrls(product, fallbackText);
  return urls[0] || `https://placehold.co/400x300?text=${encodeURIComponent(fallbackText)}`;
};

/**
 * Validate image URL format
 * @param {string} url - Image URL to validate
 * @returns {boolean} - True if valid URL
 */
export const isValidImageUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  
  // Basic URL validation
  try {
    new URL(url);
  } catch {
    return false;
  }
  
  // Check for common image file extensions
  const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$/i;
  return imageExtensions.test(url) || url.includes('placehold.co') || url.includes('unsplash');
};

/**
 * Filter and validate image URLs
 * @param {Array} urls - Array of image URLs
 * @returns {Array} - Array of valid image URLs
 */
export const filterValidImages = (urls) => {
  if (!Array.isArray(urls)) return [];
  return urls.filter(url => isValidImageUrl(url));
};

/**
 * Get product images with validation and fallback
 * @param {Object} product - Product object from backend API
 * @param {string} productName - Product name for placeholder
 * @returns {Array} - Array of validated image URLs
 */
export const getProductImages = (product, productName = 'Product') => {
  const urls = getImageUrls(product, productName);
  const validUrls = filterValidImages(urls);
  
  // Return valid URLs or fallback placeholder
  return validUrls.length > 0 
    ? validUrls 
    : [`https://placehold.co/800x600?text=${encodeURIComponent(productName)}`];
};

export default {
  getImageUrls,
  getPrimaryImage,
  isValidImageUrl,
  filterValidImages,
  getProductImages
};
