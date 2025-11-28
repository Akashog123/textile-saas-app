// src/api/apiInquiry.js
// Customer inquiry and fabric analysis API endpoints

import api from './axios';

/**
 * Submit a fabric inquiry with optional image
 * @param {Array} distributorIds - List of distributor IDs to send inquiry to
 * @param {string} message - Inquiry message
 * @param {File} [image] - Optional fabric image for review
 * @returns {Promise} Response with inquiry confirmation
 */
export const submitInquiry = (distributorIds, message, image = null) => {
    const formData = new FormData();
    formData.append('distributor_ids', JSON.stringify(distributorIds));
    formData.append('message', message);
    if (image) {
        formData.append('image', image);
    }

    return api.post('/inquiry/submit', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};

/**
 * Get inquiry history for current user
 * @returns {Promise} Response with list of inquiries
 */
export const getInquiryHistory = () => {
    return api.get('/inquiry/history');
};

export default {
    submitInquiry,
    getInquiryHistory
};
