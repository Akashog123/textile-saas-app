// src/api/apiMarketing.js
// Marketing and AI content generation API endpoints

import api from './axios';

/**
 * Generate marketing content (captions/posters) from file upload
 * @param {File} file - CSV/XLSX file with product data OR image file
 * @returns {Promise} Response with AI-generated captions or poster
 */
export const generateMarketingContent = (file) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/marketing/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000 // 60 seconds for AI processing
  });
};

/**
 * Get allowed file extensions for marketing uploads
 * @returns {Promise} Response with allowed extensions list
 */
export const getAllowedExtensions = () => {
  return api.get('/marketing/allowed-extensions');
};

export default {
  generateMarketingContent,
  getAllowedExtensions
};
