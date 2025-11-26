// src/api/apiAnalytics.js
// Business analytics and insights API endpoints

import api from './axios';

/**
 * Get top-selling products by year
 * @param {number} year - Year to get data for (optional)
 * @returns {Promise} Response with top-selling products data
 */
export const getTopSellingProducts = (year = null) => {
    const params = year ? { year } : {};
    return api.get('/top-selling-products/', { params });
};

/**
 * Get trending shops with AI insights
 * @param {Object} params - Query parameters
 * @param {number} params.limit - Number of shops to return
 * @param {string} params.region - Filter by region
 * @returns {Promise} Response with trending shops data
 */
export const getTrendingShops = (params = {}) => {
    return api.get('/trending-shops/', { params });
};

/**
 * Get regional demand heatmap data
 * @param {Object} params - Heatmap parameters
 * @param {string} params.region - Specific region (optional)
 * @param {string} params.timeframe - Time period (week, month, quarter)
 * @returns {Promise} Response with heatmap data points
 */
export const getRegionDemandHeatmap = (params = {}) => {
    return api.get('/region-demand-heatmap/', { params });
};

/**
 * Get general stores list
 * @param {Object} params - Query parameters
 * @param {number} params.limit - Number of stores to return
 * @param {number} params.offset - Pagination offset
 * @returns {Promise} Response with stores list
 */
export const getStores = (params = {}) => {
    return api.get('/stores/', { params });
};

/**
 * Generate PDF report from data
 * @param {Object} reportData - Report configuration
 * @param {string} reportData.type - Report type
 * @param {Object} reportData.data - Report data
 * @returns {Promise} Response with PDF blob
 */
export const generatePDFReport = (reportData) => {
    return api.post('/pdf/generate', reportData, {
        responseType: 'blob',
        timeout: 30000
    });
};

export default {
    getTopSellingProducts,
    getTrendingShops,
    getRegionDemandHeatmap,
    getStores,
    generatePDFReport
};
