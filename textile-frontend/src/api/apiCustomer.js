// src/api/apiCustomer.js
// Customer discovery and shop browsing API endpoints

import api from './axios';

// ============================================================================
// TRENDING & POPULAR ENDPOINTS
// ============================================================================

/**
 * Get trending fabrics with AI-generated captions
 * @returns {Promise} Response with trending fabrics list
 */
export const getTrendingFabrics = () => {
    return api.get('/customer/trending-fabrics');
};
export const getShopReviews = (shopId) => {
  return api.get(`/customer/shops/${shopId}/reviews`);
};

export const submitShopReview = (shopId, payload) => {
  return api.post(`/customer/shops/${shopId}/reviews`, payload);
};


/**
 * Get popular shops based on sales and ratings
 * @param {string} [city] - Optional city filter
 * @returns {Promise} Response with popular shops list
 */
export const getPopularShops = (city = null) => {
    const params = city ? { city } : {};
    return api.get('/customer/popular-shops', { params });
};

// ============================================================================
// SHOP BROWSING ENDPOINTS
// ============================================================================

/**
 * Get all registered shops with pagination
 * @param {Object} options - Pagination and filter options
 * @param {number} [options.page=1] - Page number
 * @param {number} [options.per_page=20] - Items per page
 * @param {string} [options.city] - Filter by city
 * @param {string} [options.category] - Filter by product category
 * @param {string} [options.sort='rating'] - Sort by: rating, name, newest
 * @returns {Promise} Response with all shops
 */
export const getAllShops = (options = {}) => {
    return api.get('/customer/shops/shops', { params: options });
};

/**
 * Get detailed information about a specific shop including products
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with shop details and products
 */
export const getShopDetails = (shopId) => {
    return api.get(`/customer/shops/shop/${shopId}`);
};

/**
 * Get products from a specific shop with filtering
 * @param {number} shopId - Shop ID
 * @param {Object} options - Filter options
 * @returns {Promise} Response with shop products
 */
export const getShopProducts = (shopId, options = {}) => {
    return api.get(`/customer/shops/shop/${shopId}/products`, { params: options });
};

// ============================================================================
// SEARCH ENDPOINTS
// ============================================================================

/**
 * Unified semantic search for shops and products
 * @param {Object} params - Search parameters
 * @param {string} params.q - Search query (required)
 * @param {string} [params.type='all'] - Search type: 'all', 'products', 'shops'
 * @param {string} [params.category] - Filter by category
 * @param {string} [params.city] - Filter by city (for shops)
 * @param {number} [params.min_price] - Minimum price (for products)
 * @param {number} [params.max_price] - Maximum price (for products)
 * @param {number} [params.min_rating] - Minimum rating
 * @param {number} [params.limit=20] - Results per type
 * @returns {Promise} Response with search results
 */
export const searchShopsAndProducts = (params) => {
    if (!params?.q || params.q.trim() === '') {
        return Promise.resolve({ data: { status: 'success', products: [], shops: [], query: '' } });
    }
    return api.get('/customer/search', { params: { ...params, q: params.q.trim() } });
};

/**
 * Get autocomplete suggestions for search
 * @param {string} query - Partial search query (min 2 chars)
 * @param {number} [limit=5] - Max suggestions per type
 * @returns {Promise} Response with product, shop, and category suggestions
 */
export const getSearchSuggestions = (query, limit = 5) => {
    if (!query || query.length < 2) {
        return Promise.resolve({ data: { products: [], shops: [], categories: [] } });
    }
    return api.get('/customer/search/suggestions', { params: { q: query, limit } });
};

// ============================================================================
// NEARBY / LOCATION BASED SEARCH
// ============================================================================

/**
 * Find nearby shops based on coordinates
 * @param {Object} params - Location parameters
 * @param {number} params.lat - Latitude (required)
 * @param {number} params.lon - Longitude (required)
 * @param {number} [params.radius=10] - Search radius in km
 * @param {string} [params.product_query] - Optional product search within nearby shops
 * @param {string} [params.category] - Filter by product category
 * @param {number} [params.limit=20] - Max results
 * @returns {Promise} Response with nearby shops
 */
export const getNearbyShops = (params) => {
    const { lat, lon, radius = 10, product_query, category, limit = 20 } = params;
    return api.get('/customer/search/nearby', {
        params: { lat, lon, radius, product_query, category, limit }
    });
};

/**
 * Find nearby shops with specific product search (POST method)
 * @param {Object} data - Search data
 * @returns {Promise} Response with nearby shops and matching products
 */
export const searchNearbyWithProducts = (data) => {
    return api.post('/customer/search/nearby', data);
};

// ============================================================================
// IMAGE SEARCH
// ============================================================================

/**
 * Search for visually similar products using an image
 * Searches real shop products by visual similarity
 * @param {File} imageFile - Image file to search with
 * @param {number} [limit=20] - Max results
 * @returns {Promise} Response with similar products
 */
export const searchByImage = async (imageFile, limit = 20) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('limit', limit);
    
    return api.post('/image-search/similar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 15000 // 15 second timeout
    });
};

/**
 * Get image search service status
 * @returns {Promise} Response with service status
 */
export const getImageSearchStatus = () => {
    return api.get('/image-search/status');
};

// ============================================================================
// PRODUCT BROWSING ENDPOINTS
// ============================================================================

/**
 * Browse products with filtering and pagination
 * @param {Object} options - Filter options
 * @param {number} [options.page=1] - Page number
 * @param {number} [options.per_page=20] - Items per page
 * @param {string} [options.category] - Filter by category
 * @param {string} [options.search] - Search text
 * @param {number} [options.min_price] - Minimum price
 * @param {number} [options.max_price] - Maximum price
 * @param {string} [options.sort='rating'] - Sort: rating, price_asc, price_desc, newest
 * @returns {Promise} Response with products
 */
export const browseProducts = (options = {}) => {
    return api.get('/customer/products', { params: options });
};

/**
 * Get detailed product information
 * @param {number} productId - Product ID
 * @returns {Promise} Response with product details, reviews, and similar products
 */
export const getProductDetails = (productId) => {
    return api.get(`/customer/products/${productId}`);
};

/**
 * Get all product categories with counts
 * @returns {Promise} Response with categories
 */
export const getCategories = () => {
    return api.get('/customer/categories');
};

// ============================================================================
// SERVICE STATUS
// ============================================================================

/**
 * Get search service status
 * @returns {Promise} Response with search service status
 */
export const getSearchStatus = () => {
    return api.get('/customer/search/status');
};

export default {
    // Trending & Popular
    getTrendingFabrics,
    getPopularShops,
    // Shop Browsing
    getAllShops,
    getShopDetails,
    getShopProducts,
    // Search
    searchShopsAndProducts,
    getSearchSuggestions,
    // Location Based
    getNearbyShops,
    searchNearbyWithProducts,
    // Image Search
    searchByImage,
    getImageSearchStatus,
    // Product Browsing
    browseProducts,
    getProductDetails,
    getCategories,
    // Status
    getSearchStatus
};
