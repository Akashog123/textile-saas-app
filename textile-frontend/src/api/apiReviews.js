// src/api/apiReviews.js
// Customer Review API for Shops

import api from './axios';

/**
 * Get all reviews for a specific shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with shop reviews, avgRating, reviewCount
 */
export const getShopReviews = (shopId) => {
    return api.get(`/customer/shops/${shopId}/reviews`);
};

/**
 * Submit a review for a shop (requires authentication)
 * @param {number} shopId - Shop ID
 * @param {Object} reviewData - Review data
 * @param {number} reviewData.rating - Rating (1-5)
 * @param {string} [reviewData.title] - Review title (optional)
 * @param {string} reviewData.comment - Review body text
 * @returns {Promise} Response with created review
 */
export const submitShopReview = (shopId, reviewData) => {
    return api.post(`/customer/shops/${shopId}/reviews`, {
        rating: reviewData.rating,
        title: reviewData.title || '',
        comment: reviewData.comment || reviewData.body
    });
};

/**
 * Create a review for a shop (alias for submitShopReview for API compatibility)
 * @param {Object} data - Review data with shop_id
 * @returns {Promise} Response with created review
 */
export const createReview = (data) => {
    return api.post(`/customer/shops/${data.shop_id}/reviews`, {
        rating: data.rating,
        title: data.title || '',
        comment: data.body || data.comment
    });
};

/**
 * Submit a review for a shop or product (backwards compatibility)
 * @param {Object} reviewData - Review data
 * @param {number} [reviewData.shop_id] - Shop ID (for shop reviews)
 * @param {number} [reviewData.product_id] - Product ID (for product reviews)
 * @param {number} reviewData.rating - Rating (1-5)
 * @param {string} [reviewData.title] - Review title
 * @param {string} [reviewData.body] - Review body text
 * @returns {Promise} Response with created review
 */
export const submitReview = (reviewData) => {
    if (reviewData.shop_id) {
        return api.post(`/customer/shops/${reviewData.shop_id}/reviews`, {
            rating: reviewData.rating,
            title: reviewData.title || '',
            comment: reviewData.body || reviewData.comment
        });
    }
    return api.post('/reviews/submit', reviewData);
};

/**
 * Get all reviews submitted by the current authenticated user
 * @returns {Promise} Response with user's reviews
 */
export const getMyReviews = () => {
    return api.get('/customer/reviews/my-reviews');
};

/**
 * Update an existing review by review ID only
 * @param {number} reviewId - Review ID
 * @param {Object} reviewData - Updated review data
 * @returns {Promise} Response with updated review
 */
export const updateReviewById = (reviewId, reviewData) => {
    return api.put(`/customer/reviews/${reviewId}`, {
        rating: reviewData.rating,
        title: reviewData.title,
        body: reviewData.body || reviewData.comment
    });
};

/**
 * Update an existing review with shop_id in URL (for frontend compatibility)
 * @param {number} shopId - Shop ID
 * @param {number} reviewId - Review ID
 * @param {Object} reviewData - Updated review data
 * @returns {Promise} Response with updated review
 */
export const updateReview = (shopId, reviewId, reviewData) => {
    return api.put(`/customer/shops/${shopId}/reviews/${reviewId}`, {
        rating: reviewData.rating,
        title: reviewData.title,
        body: reviewData.body || reviewData.comment
    });
};

/**
 * Delete a review by review ID only (legacy route)
 * @param {number} reviewId - Review ID
 * @returns {Promise} Response with deletion status
 */
export const deleteReviewById = (reviewId) => {
    return api.delete(`/customer/reviews/${reviewId}`);
};

/**
 * Delete a review with shop_id in URL (for frontend compatibility)
 * @param {number} shopId - Shop ID
 * @param {number} reviewId - Review ID
 * @returns {Promise} Response with deletion status
 */
export const deleteReview = (shopId, reviewId) => {
    return api.delete(`/customer/shops/${shopId}/reviews/${reviewId}`);
};

/**
 * Get trending/popular shops based on reviews (aggregate insights)
 * @returns {Promise} Response with popular shops data
 */
export const getPopularShops = () => {
    return api.get('/customer/popular-shops');
};

export default {
    getShopReviews,
    submitShopReview,
    submitReview,
    createReview,
    getMyReviews,
    updateReview,
    updateReviewById,
    deleteReview,
    deleteReviewById,
    getPopularShops
};
