// src/api/apiReviews.js

import api from './axios';

/**
 * Get all reviews for a specific shop
 * @param {number} shopId
 * @returns {Promise}
 */
export const getShopReviews = (shopId) => {
  return api.get(`/customer/shops/${shopId}/reviews`);
};

/**
 * Create a shop review
 * @param {object} data
 * @returns {Promise}
 */
export const createReview = (data) => {
  return api.post(`/customer/shops/${data.shop_id}/reviews`, data);
};

/**
 * Update a shop review
 * @param {number} shopId
 * @param {number} reviewId
 * @param {object} data
 * @returns {Promise}
 */
export const updateReview = (shopId, reviewId, data) => {
  return api.put(`/customer/shops/${shopId}/reviews/${reviewId}`, data);
};

/**
 * Delete a shop review
 * @param {number} shopId
 * @param {number} reviewId
 * @returns {Promise}
 */
export const deleteReview = (shopId, reviewId) => {
  return api.delete(`/customer/shops/${shopId}/reviews/${reviewId}`);
};

export default {
  getShopReviews,
  createReview,
  updateReview,
  deleteReview
};
