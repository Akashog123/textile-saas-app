// src/api/apiCustomer.js
// Customer discovery and shop browsing API endpoints

import api from './axios';

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
 * @returns {Promise} Response with popular shops list
 */
export const getPopularShops = () => {
    return api.get('/customer/popular-shops');
};

/**
 * Get all registered shops
 * @returns {Promise} Response with all shops
 */
export const getAllShops = () => {
    return api.get('/customer/shops/shops');
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
 * Search for shops and products by keyword
 * @param {string} query - Search query
 * @returns {Promise} Response with matching shops and products
 */
export const searchShopsAndProducts = (query) => {
    if (!query || query.trim() === '') {
        return Promise.resolve({ data: { status: 'success', shops: [], products: [] } });
    }
    return api.get('/customer/search', { params: { q: query.trim() } });
};

/**
 * Find nearby shops based on coordinates
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {number} radius - Search radius in meters (default: 3000)
 * @returns {Promise} Response with nearby shops
 */
export const getNearbyShops = (lat, lon, radius = 3000) => {
    return api.get('/customer/nearby-shops', {
        params: { lat, lon, radius }
    });
};

export default {
    getTrendingFabrics,
    getPopularShops,
    getAllShops,
    getShopDetails,
    searchShopsAndProducts,
    getNearbyShops
};
