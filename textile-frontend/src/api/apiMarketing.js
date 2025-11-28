// src/api/apiMarketing.js
// Marketing and AI content generation API endpoints

import api from './axios';

/**
 * Generate marketing content (captions/posters) from file upload
 * @param {FormData} formData - FormData with file and optional product details
 * @returns {Promise} Response with AI-generated captions or poster
 */
export const generateMarketingContent = (formData) => {
  return api.post('/marketing/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000 // 2 minutes for batch AI processing
  });
};

/**
 * Get marketing content generation template
 * @returns {Promise} Response with template file URL and format information
 */
export const getMarketingTemplate = () => {
  return api.get('/marketing/template');
};

/**
 * Get marketing content generation progress
 * @returns {Promise} Response with progress information
 */
export const getGenerationProgress = () => {
  return api.get('/marketing/progress');
};

/**
 * Reset marketing content generation progress
 * @returns {Promise} Response confirming reset
 */
export const resetGenerationProgress = () => {
  return api.post('/marketing/progress/reset');
};

/**
 * Get marketing content generation history
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (default: 1)
 * @param {number} params.per_page - Items per page (default: 10)
 * @returns {Promise} Response with paginated history data
 */
export const getMarketingHistory = (params = {}) => {
  return api.get('/marketing/history', { params });
};

/**
 * Get allowed file extensions for marketing uploads
 * @returns {Promise} Response with allowed extensions list
 */
export const getAllowedExtensions = () => {
  return api.get('/marketing/allowed-extensions');
};

/**
 * Delete marketing history item
 * @param {string} itemId - ID of the history item to delete
 * @returns {Promise} Response with deletion status
 */
export const deleteMarketingHistoryItem = (itemId) => {
  return api.delete(`/marketing/history/${itemId}`);
};

export default {
  generateMarketingContent,
  getMarketingTemplate,
  getMarketingHistory,
  getAllowedExtensions,
  deleteMarketingHistoryItem
};
