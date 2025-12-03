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

// ============================================================================
// CHAT / CONVERSATION ENDPOINTS
// ============================================================================

/**
 * Get all conversation threads for the current user
 * @returns {Promise} Response with list of conversations
 */
export const getConversations = () => {
    return api.get('/inquiry/conversations');
};

/**
 * Get all messages for a specific conversation
 * @param {number} conversationId - The conversation/thread ID
 * @returns {Promise} Response with messages array
 */
export const getConversationMessages = (conversationId) => {
    return api.get(`/inquiry/conversation/${conversationId}/messages`);
};

/**
 * Send a new message in a conversation
 * @param {number} conversationId - The conversation/thread ID
 * @param {string} message - The message text
 * @param {File} [image] - Optional image attachment
 * @returns {Promise} Response with sent message data
 */
export const sendMessage = (conversationId, message, image = null) => {
    const formData = new FormData();
    formData.append('message', message);
    if (image) {
        formData.append('image', image);
    }

    return api.post(`/inquiry/conversation/${conversationId}/send`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};

/**
 * Mark all messages in a conversation as read
 * @param {number} conversationId - The conversation/thread ID
 * @returns {Promise} Response with success status
 */
export const markConversationRead = (conversationId) => {
    return api.put(`/inquiry/conversation/${conversationId}/mark-read`);
};

/**
 * Get total unread message count for the current user
 * @returns {Promise} Response with unread count
 */
export const getUnreadCount = () => {
    return api.get('/inquiry/unread-count');
};

export default {
    submitInquiry,
    getInquiryHistory,
    getConversations,
    getConversationMessages,
    sendMessage,
    markConversationRead,
    getUnreadCount
};
