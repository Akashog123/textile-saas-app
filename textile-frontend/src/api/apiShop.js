// src/api/apiShop.js
// Shop dashboard and sales analytics API endpoints

import api from './axios';

/**
 * Get shop dashboard analytics and insights
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with dashboard data including sales, revenue, AI insights, and forecast
 */
export const getShopDashboard = (shopId) => {
    return api.get(`/shop/dashboard`, { 
        params: { shop_id: shopId },
        timeout: 30000
    });
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

/**
 * Get distributors for search
 * @param {string} search - Search term (optional)
 * @returns {Promise} Response with list of distributors
 */
export const getDistributors = (search = '') => {
    return api.get(`/shop/distributors`, {
        params: { search }
    });
};

/**
 * Get next quarter demand forecast
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with demand forecast data
 */
export const getDemandForecast = (shopId) => {
    return api.get(`/shop/demand-forecast`, {
        params: { shop_id: shopId }
    });
};


/* -------------------------
   Owner's shops (my-shops)
   CRUD helpers used by shop profile UI
   ------------------------- */

/**
 * Get all shops for current logged-in owner
 * - backend: GET /shop/my-shops
 */
export const getMyShops = (params = {}) => {
  // params can include page, per_page, etc.
  return api.get('/shop/my-shops', { params, timeout: 15000 });
};

/**
 * Create a new shop
 * - backend: POST /shop/my-shops
 * - If sending image(s), pass FormData and set `isMultipart=true`.
 * - Example shopData (JSON): { name, description, address, lat, lon, gstin, contact }
 */
export const createShop = (shopData, { isMultipart = false } = {}) => {
  if (isMultipart) {
    const fd = new FormData();
    Object.entries(shopData).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, v);
    });
    return api.post('/shop/my-shops', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  } else {
    return api.post('/shop/my-shops', shopData, { timeout: 15000 });
  }
};

/**
 * Update shop
 * - backend: PUT /shop/my-shops/:id
 * - pass shopData similar to createShop
 */
export const updateShop = (shopId, shopData, { isMultipart = false } = {}) => {
  if (isMultipart) {
    const fd = new FormData();
    Object.entries(shopData).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, v);
    });
    return api.put(`/shop/my-shops/${shopId}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  } else {
    return api.put(`/shop/my-shops/${shopId}`, shopData, { timeout: 15000 });
  }
};

/**
 * Delete a shop
 * - backend: DELETE /shop/my-shops/:id
 */
export const deleteShop = (shopId) => {
  return api.delete(`/shop/my-shops/${shopId}`, { timeout: 15000 });
};


export default {
    getShopDashboard,
    uploadSalesData,
    exportSalesData,
    getDistributors,
    getDemandForecast,
    getMyShops,
    createShop,
    updateShop,
    deleteShop,
};