// src/api/apiReviews.js
// Review system API endpoints (Story 8)

import api from './axios';

/**
 * Submit a review for a shop or product
 * @param {Object} reviewData - Review data
 * @param {number} [reviewData.shop_id] - Shop ID (for shop reviews)
 * @param {number} [reviewData.product_id] - Product ID (for product reviews)
 * @param {number} reviewData.rating - Rating (1-5)
 * @param {string} [reviewData.title] - Review title
 * @param {string} [reviewData.body] - Review body text
 * @returns {Promise} Response with created review
 */
export const submitReview = (reviewData) => {
    return api.post('/reviews/submit', reviewData);
};

/**
 * Create a shop review (alias for submitReview for backwards compatibility)
 * @param {object} data
 * @returns {Promise}
 */
export const createReview = (data) => {
    return api.post('/reviews/submit', data);
};

/**
 * Get all reviews for a specific shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with shop reviews and stats
 */
export const getShopReviews = (shopId) => {
    return api.get(`/reviews/shop/${shopId}`);
};

/**
 * Get all reviews for a specific product
 * @param {number} productId - Product ID
 * @returns {Promise} Response with product reviews and stats
 */
export const getProductReviews = (productId) => {
    return api.get(`/reviews/product/${productId}`);
};

/**
 * Get all reviews submitted by the current user
 * @returns {Promise} Response with user's reviews
 */
export const getMyReviews = () => {
    return api.get('/reviews/my-reviews');
};

/**
 * Update a shop review
 * @param {number} shopId
 * @param {number} reviewId
 * @param {object} data
 * @returns {Promise}
 */
export const updateReview = (shopId, reviewId, data) => {
    return api.put(`/reviews/${reviewId}`, data);
};

/**
 * Delete a review (only the reviewer can delete their own review)
 * @param {number} reviewId - Review ID
 * @returns {Promise} Response with deletion status
 */
export const deleteReview = (reviewId) => {
    return api.delete(`/reviews/${reviewId}`);
};

/**
 * Get trending patterns based on reviews (aggregate insights)
 * @returns {Promise} Response with trending patterns
 */
export const getTrendingPatterns = () => {
    return api.get('/customer/popular-shops');
};

export default {
    submitReview,
    createReview,
    getShopReviews,
    getProductReviews,
    getMyReviews,
    updateReview,
    deleteReview,
    getTrendingPatterns
};
