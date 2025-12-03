// src/api/apiAI.js
// AI-powered search and analysis API endpoints

import api from './axios';

/**
 * Find stores using AI-powered text or voice search
 * @param {Object} params - Search parameters
 * @param {string} params.prompt - Text description of requirements
 * @param {File} params.voiceFile - Audio file (optional)
 * @returns {Promise} Response with AI-matched stores
 */
export const findStoresWithAI = (params) => {
    if (params.voiceFile) {
        const formData = new FormData();
        formData.append('prompt', params.prompt || '');
        formData.append('voice', params.voiceFile);
        
        return api.post('/ai-find-stores/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    } else {
        return api.post('/ai-find-stores/', { prompt: params.prompt });
    }
};

/**
 * @deprecated Use searchByImage from apiCustomer.js instead
 * Compare uploaded image against product catalog
 * @param {File} imageFile - Image file to compare
 * @returns {Promise} Response with similar fabric recommendations
 */
export const compareImageWithCatalog = (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('limit', 20);
    
    return api.post('/image-search/similar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 15000
    });
};

/**
 * Generate AI-powered marketing content
 * @param {Object} params - Marketing generation parameters
 * @param {File} params.image - Product image (optional)
 * @param {string} params.type - Content type (caption, poster, trends)
 * @returns {Promise} Response with AI-generated marketing content
 */
export const generateMarketingContent = (params) => {
    if (params.image) {
        const formData = new FormData();
        formData.append('image', params.image);
        formData.append('type', params.type || 'caption');
        
        return api.post('/marketing/generate', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000 // Allow 60 seconds for AI processing
        });
    } else {
        return api.post('/marketing/generate', { type: params.type || 'caption' });
    }
};

/**
 * Get allowed file extensions for marketing uploads
 * @returns {Promise} Response with supported file types
 */
export const getAllowedExtensions = () => {
    return api.get('/marketing/allowed-extensions');
};

export default {
    findStoresWithAI,
    compareImageWithCatalog,
    generateMarketingContent,
    getAllowedExtensions
};
