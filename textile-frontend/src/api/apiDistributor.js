// src/api/apiDistributor.js
// Distributor/Manufacturer analytics and planning API endpoints

import api from './axios';

/**
 * Get stock heatmap data from database for the logged-in distributor
 * Returns shop locations with stock health status based on inventory vs safety_stock
 * @returns {Promise} Response with stock heatmap points and summary
 */
export const getDistributorStockHeatmap = () => {
    return api.get('/distributor/stock-heatmap', {
        timeout: 60000
    });
};

/**
 * Get AI-powered stock planning insights from database data
 * @param {Object} stockData - The stock heatmap data object with heatmapPoints and summary
 * @returns {Promise} Response with AI insights, forecasts, recommendations
 */
export const getAIStockPlanning = (stockData) => {
    return api.post('/distributor/ai-stock-planning', stockData, {
        timeout: 120000
    });
};

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
 * Get heatmap data for regional demand visualization
 * @param {File} file - CSV/Excel file with regional sales data (Date, Product, Region, Sales, Quantity)
 * @returns {Promise} Response with heatmap points containing coordinates and intensity
 */
export const getRegionalDemandHeatmap = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post('/distributor/regional-demand-heatmap', formData, {
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
 * Get AI-powered production planning insights from heatmap data
 * @param {Object} heatmapData - The heatmap data object with heatmapPoints and summary
 * @returns {Promise} Response with AI insights, forecasts, recommendations
 */
export const getAIProductionPlanning = (heatmapData) => {
    return api.post('/distributor/ai-production-planning', heatmapData, {
        timeout: 60000
    });
};

/**
 * Get sample data format for uploads
 * @returns {Promise} Response with sample format info
 */
export const getSampleFormat = () => {
    return api.get('/distributor/sample-format');
};

/**
 * Get AI-powered demand forecast for products
 * @param {Object} data - Optional filters
 * @returns {Promise} Response with demand forecasts and AI analysis
 */
export const getAIDemandForecast = (data = {}) => {
    return api.post('/distributor/ai-demand-forecast', data, {
        timeout: 120000
    });
};

/**
 * Get AI-powered revenue impact analysis
 * @param {Object} data - Optional filters
 * @returns {Promise} Response with revenue impacts and AI analysis
 */
export const getAIRevenueImpact = (data = {}) => {
    return api.post('/distributor/ai-revenue-impact', data, {
        timeout: 120000
    });
};

/**
 * Send message to AI chat assistant
 * @param {string} message - User's question
 * @param {Object} context - Optional AI insights context (demand forecast, stock impact, etc.)
 * @returns {Promise} Response with AI answer
 */
export const sendAIChatMessage = (message, context = null) => {
    return api.post('/distributor/ai-chat', { message, context }, {
        timeout: 120000
    });
};

export default {
    getDistributorStockHeatmap,
    getAIStockPlanning,
    analyzeRegionalDemand,
    getRegionalDemandHeatmap,
    generateProductionPlan,
    exportProductionPlan,
    downloadRegionalReport,
    getAIProductionPlanning,
    getSampleFormat,
    getAIDemandForecast,
    getAIRevenueImpact,
    sendAIChatMessage
};
