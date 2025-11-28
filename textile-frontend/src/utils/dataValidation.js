/**
 * Robust data validation utilities for frontend-backend consistency
 * Handles missing fields, type validation, and graceful fallbacks
 */

/**
 * Validate and normalize product data from backend
 * @param {Object} product - Raw product data from backend API
 * @returns {Object} - Normalized product data with all required fields
 */
export const validateProductData = (product) => {
  if (!product || typeof product !== 'object') {
    return createFallbackProduct();
  }

  return {
    id: validateId(product.id),
    name: validateString(product.name, 'Unknown Product'),
    price: validatePrice(product.price),
    description: validateString(product.description, 'No description available'),
    category: validateString(product.category, 'General'),
    rating: validateRating(product.rating),
    seller: validateString(product.seller, 'Independent Seller'),
    badge: validateString(product.badge, ''),
    is_trending: Boolean(product.is_trending),
    is_active: product.is_active !== false, // Default to true
    shop_id: validateId(product.shop_id),
    shop_location: validateString(product.shop_location, 'Unknown'),
    shop_city: validateString(product.shop_city, 'Unknown'),
    ai_caption: validateString(product.ai_caption, product.description || 'No description available'),
    imageUrls: validateImageUrls(product)
  };
};

/**
 * Validate and normalize shop data from backend
 * @param {Object} shop - Raw shop data from backend API
 * @returns {Object} - Normalized shop data with all required fields
 */
export const validateShopData = (shop) => {
  if (!shop || typeof shop !== 'object') {
    return createFallbackShop();
  }

  return {
    id: validateId(shop.id),
    name: validateString(shop.name, 'Unknown Shop'),
    description: validateString(shop.description, 'Quality textile shop'),
    address: validateString(shop.address, 'Address not available'),
    contact: validateString(shop.contact, 'Contact not available'),
    hours: validateString(shop.hours, 'Open during business hours'),
    rating: validateRating(shop.rating),
    location: validateString(shop.location, shop.address || 'Location not available'),
    city: validateString(shop.city, 'Unknown'),
    image: validateString(shop.image_url || shop.image, `https://placehold.co/800x600?text=${encodeURIComponent(shop.name || 'Shop')}`),
    lat: validateCoordinate(shop.lat || shop.latitude),
    lng: validateCoordinate(shop.lng || shop.longitude),
    products: Array.isArray(shop.products) ? shop.products.map(validateProductData) : []
  };
};

/**
 * Validate and normalize fabric data from trending endpoints
 * @param {Object} fabric - Raw fabric data from backend API
 * @returns {Object} - Normalized fabric data with all required fields
 */
export const validateFabricData = (fabric) => {
  if (!fabric || typeof fabric !== 'object') {
    return createFallbackFabric();
  }

  return {
    id: validateId(fabric.id),
    name: validateString(fabric.name, 'Unknown Fabric'),
    price: validatePrice(fabric.price),
    description: validateString(fabric.description, fabric.ai_caption || 'No description available'),
    category: validateString(fabric.category, 'General'),
    rating: validateRating(fabric.rating),
    badge: validateString(fabric.badge, 'Trending'),
    seller: validateString(fabric.seller, 'Independent Seller'),
    image: validateString(fabric.image, `https://placehold.co/800x600?text=${encodeURIComponent(fabric.name || 'Fabric')}`),
    ai_caption: validateString(fabric.ai_caption, fabric.description || 'No description available')
  };
};

/**
 * Validate ID field (integer or string)
 * @param {*} id - ID value to validate
 * @returns {number|string} - Validated ID
 */
const validateId = (id) => {
  if (id === null || id === undefined) return 0;
  if (typeof id === 'number' && !isNaN(id)) return id;
  if (typeof id === 'string') {
    const num = parseInt(id, 10);
    return isNaN(num) ? id : num;
  }
  return 0;
};

/**
 * Validate string field
 * @param {*} value - Value to validate
 * @param {string} fallback - Fallback value
 * @returns {string} - Validated string
 */
const validateString = (value, fallback = '') => {
  if (typeof value === 'string') return value.trim();
  if (value !== null && value !== undefined) return String(value);
  return fallback;
};

/**
 * Validate price field (formatted string or number)
 * @param {*} price - Price value to validate
 * @returns {string} - Validated price string
 */
const validatePrice = (price) => {
  if (typeof price === 'string') {
    // Check if it's already formatted (contains currency symbol)
    if (price.includes('₹') || price.includes('$') || price.includes('€')) {
      return price;
    }
    // Try to parse as number and format
    const num = parseFloat(price.replace(/[^\d.]/g, ''));
    if (!isNaN(num) && num > 0) {
      return `₹${num.toLocaleString()}`;
    }
  } else if (typeof price === 'number' && !isNaN(price) && price > 0) {
    return `₹${price.toLocaleString()}`;
  }
  return 'Price not available';
};

/**
 * Validate rating field
 * @param {*} rating - Rating value to validate
 * @returns {number} - Validated rating (0-5)
 */
const validateRating = (rating) => {
  if (typeof rating === 'number' && !isNaN(rating)) {
    return Math.max(0, Math.min(5, rating));
  }
  if (typeof rating === 'string') {
    const num = parseFloat(rating);
    if (!isNaN(num)) {
      return Math.max(0, Math.min(5, num));
    }
  }
  return 4.0; // Default rating
};

/**
 * Validate coordinate field
 * @param {*} coord - Coordinate value to validate
 * @returns {number|null} - Validated coordinate or null
 */
const validateCoordinate = (coord) => {
  if (typeof coord === 'number' && !isNaN(coord)) {
    return coord;
  }
  if (typeof coord === 'string') {
    const num = parseFloat(coord);
    if (!isNaN(num)) {
      return num;
    }
  }
  return null;
};

/**
 * Validate image URLs array
 * @param {Object} product - Product object with image data
 * @returns {Array} - Array of validated image URLs
 */
const validateImageUrls = (product) => {
  const urls = [];
  
  // Handle various image field formats
  if (product.imageUrls && Array.isArray(product.imageUrls)) {
    urls.push(...product.imageUrls.filter(url => typeof url === 'string' && url.trim()));
  }
  
  if (product.image_url && typeof product.image_url === 'string') {
    urls.push(product.image_url);
  }
  
  if (product.image && typeof product.image === 'string') {
    urls.push(product.image);
  }
  
  if (product.images && Array.isArray(product.images)) {
    product.images.forEach(img => {
      const url = img.url || img;
      if (typeof url === 'string' && url.trim()) {
        urls.push(url);
      }
    });
  }
  
  // Return valid URLs or fallback placeholder
  return urls.length > 0 
    ? urls 
    : [`https://placehold.co/800x600?text=${encodeURIComponent(product.name || 'Product')}`];
};

/**
 * Create fallback product data
 * @returns {Object} - Fallback product object
 */
const createFallbackProduct = () => ({
  id: 0,
  name: 'Product Not Available',
  price: 'Price not available',
  description: 'This product information is currently unavailable.',
  category: 'Unknown',
  rating: 4.0,
  seller: 'Independent Seller',
  badge: '',
  is_trending: false,
  is_active: true,
  shop_id: 0,
  shop_location: 'Unknown',
  shop_city: 'Unknown',
  ai_caption: 'Product information not available',
  imageUrls: ['https://placehold.co/800x600?text=Product+Not+Available']
});

/**
 * Create fallback shop data
 * @returns {Object} - Fallback shop object
 */
const createFallbackShop = () => ({
  id: 0,
  name: 'Shop Not Available',
  description: 'Shop information is currently unavailable.',
  address: 'Address not available',
  contact: 'Contact not available',
  hours: 'Open during business hours',
  rating: 4.0,
  location: 'Location not available',
  city: 'Unknown',
  image: 'https://placehold.co/800x600?text=Shop+Not+Available',
  lat: null,
  lng: null,
  products: []
});

/**
 * Create fallback fabric data
 * @returns {Object} - Fallback fabric object
 */
const createFallbackFabric = () => ({
  id: 0,
  name: 'Fabric Not Available',
  price: 'Price not available',
  description: 'Fabric information is currently unavailable.',
  category: 'Unknown',
  rating: 4.0,
  badge: 'Trending',
  seller: 'Independent Seller',
  image: 'https://placehold.co/800x600?text=Fabric+Not+Available',
  ai_caption: 'Fabric information not available'
});

export default {
  validateProductData,
  validateShopData,
  validateFabricData,
  validateId,
  validateString,
  validatePrice,
  validateRating,
  validateCoordinate,
  validateImageUrls
};
