// src/api/ap iDistributor.js
// Distributor/Manufacturer analytics and planning API endpoints

import api from './axios';

/**
 * Analyze regional demand from uploaded sales data
 * @param {File} file - CSV/Excel file with regional sales data
 * @returns {Promise} Response with regional analysis, demand summary, and AI insights
 */
export const analyzeRegionalDemand = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post('/distributor/regional-demand', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
    });
};

/**
 * Generate production plan from sales data
 * @param {File} file - CSV/Excel file with sales data
 * @returns {Promise} Response with production priorities and recommendations
 */
export const generateProductionPlan = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post('/distributor/production-plan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
    });
};

/**
 * Export production plan as CSV
 * @returns {Promise} Response with file blob
 */
export const exportProductionPlan = () => {
    return api.get('/distributor/export-plan', {
        responseType: 'blob'
    });
};

/**
 * Download regional demand report PDF
 * @returns {Promise} Response with PDF blob
 */
export const downloadRegionalReport = () => {
    return api.get('/distributor/regional-report', {
        responseType: 'blob'
    });
};

/**
 * Get sample data format for uploads
 * @returns {Promise} Response with sample format info
 */
export const getSampleFormat = () => {
    return api.get('/distributor/sample-format');
};

export default {
    analyzeRegionalDemand,
    generateProductionPlan,
    exportProductionPlan,
    downloadRegionalReport,
    getSampleFormat
};
