// src/api/apiProducts.js
// Product catalog and discovery API endpoints

import api from './axios';

/**
 * Get products with optional filters
 * @param {Object} params - Filter parameters
 * @param {string} params.category - Filter by category
 * @param {number} params.price_min - Minimum price filter
 * @param {number} params.price_max - Maximum price filter
 * @param {string} params.search - Search keyword
 * @returns {Promise} Response with filtered products
 */
export const getProducts = (params = {}) => {
    // Remove empty params
    const cleanParams = Object.keys(params).reduce((acc, key) => {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            acc[key] = params[key];
        }
        return acc;
    }, {});

    return api.get('/products/', { params: cleanParams });
};

/**
 * Get detailed information about a specific product
 * @param {number} productId - Product ID
 * @returns {Promise} Response with product details
 */
export const getProductDetails = (productId) => {
    return api.get(`/products/${productId}`);
};

/**
 * Get AI-driven suggested/trending products
 * @returns {Promise} Response with suggested products
 */
export const getSuggestedProducts = () => {
    return api.get('/products/suggested');
};

/**
 * View product catalog with pagination
 * @param {number} limit - Number of products to return (default: 50)
 * @returns {Promise} Response with catalog products
 */
export const viewCatalog = (limit = 50) => {
    return api.get('/catalog/view', { params: { limit } });
};

/**
 * Search product catalog with filters
 * @param {Object} params - Search parameters
 * @param {string} params.keyword - Search keyword (required)
 * @param {string} params.category - Filter by category
 * @param {string} params.color - Filter by color
 * @param {string} params.gender - Filter by gender
 * @param {string} params.season - Filter by season
 * @param {string} params.usage - Filter by usage
 * @returns {Promise} Response with search results
 */
export const searchCatalog = (params) => {
    if (!params.keyword || params.keyword.trim() === '') {
        return Promise.reject(new Error('Keyword is required for catalog search'));
    }

    return api.get('/catalog/search', { params });
};

export default {
    getProducts,
    getProductDetails,
    getSuggestedProducts,
    viewCatalog,
    searchCatalog
};
