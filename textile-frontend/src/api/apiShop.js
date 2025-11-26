// src/api/apiShop.js
// Shop dashboard and sales analytics API endpoints

import api from './axios';

/**
 * Get shop dashboard analytics and insights
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with dashboard data including sales, revenue, AI insights, and forecast
 */
export const getShopDashboard = (shopId) => {
    return api.get(`/shop/dashboard`, { params: { shop_id: shopId } });
};

/**
 * Upload sales data CSV/Excel file
 * @param {number} shopId - Shop ID
 * @param {File} file - CSV or Excel file containing sales data
 * @returns {Promise} Response with upload status and rows processed
 */
export const uploadSalesData = (shopId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('shop_id', shopId);

    return api.post('/shop/upload_sales_data', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000 // 60 seconds for file upload
    });
};

/**
 * Export sales data as CSV
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with file blob
 */
export const exportSalesData = (shopId) => {
    return api.get(`/shop/sales/export`, {
        params: { shop_id: shopId },
        responseType: 'blob'
    });
};

export default {
    getShopDashboard,
    uploadSalesData,
    exportSalesData
};
