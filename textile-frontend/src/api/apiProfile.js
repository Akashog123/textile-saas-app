// src/api/apiProfile.js
// User profile management API endpoints

import api from './axios';

/**
 * Get current user profile
 * @returns {Promise} Response with user profile data
 */
export const getProfile = () => {
    return api.get('/profile/');
};

/**
 * Update user profile
 * @param {Object} updates - Profile fields to update
 * @param {string} [updates.full_name] - Full name
 * @param {string} [updates.email] - Email address
 * @param {string} [updates.contact] - Phone number
 * @param {string} [updates.address] - Address
 * @returns {Promise} Response with updated profile
 */
export const updateProfile = (updates) => {
    return api.put('/profile/update', updates);
};

/**
 * Set primary/active shop for the user
 * @param {number} shopId - The shop ID to set as primary
 * @returns {Promise} Response with confirmation
 */
export const setPrimaryShop = (shopId) => {
    return api.put('/profile/primary-shop', { shop_id: shopId });
};

export default {
    getProfile,
    updateProfile,
    setPrimaryShop
};
