// src/api/apiShop.js
// Shop dashboard and sales analytics API endpoints

import api from './axios';

/**
 * Download CSV template for sales data upload
 * Template columns: date, sku, product_name, category, quantity_sold, selling_price, region
 * @returns {Promise} Response with CSV file blob
 */
export const downloadSalesTemplate = () => {
    return api.get('/inventory/template/sales', { responseType: 'blob' });
};

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
        timeout: 120000 // 120 seconds for file upload + AI analysis
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

/**
 * Get comprehensive weekly sales summary (Last 7 days)
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with sales summary including metrics, daily breakdown, insights
 */
export const getSalesSummary = (shopId) => {
    return api.get(`/shop/sales-summary`, {
        params: { shop_id: shopId },
        timeout: 15000
    });
};

/**
 * Get next quarter (90 days) demand forecast with confidence intervals
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with weekly/monthly forecasts, category predictions, insights
 */
export const getQuarterlyForecast = (shopId) => {
    return api.get(`/shop/quarterly-forecast`, {
        params: { shop_id: shopId },
        timeout: 30000
    });
};

/**
 * Get sales growth trend data for charting
 * @param {number} shopId - Shop ID
 * @param {string} period - 'weekly', 'monthly', or 'yearly'
 * @returns {Promise} Response with chart data, labels, SVG paths, and growth metrics
 */
export const getSalesGrowthTrend = (shopId, period = 'weekly') => {
    return api.get(`/shop/sales-growth-trend`, {
        params: { shop_id: shopId, period },
        timeout: 15000
    });
};

export const generateSalesReportPdf = (payload) => {
    return api.post('/pdf/generate', payload, {
        responseType: 'blob'
    });
};

export const getSalesUploadLogs = (shopId, limit = 5) => {
    return api.get(`/shop/upload_sales_data/logs`, {
        params: { shop_id: shopId, limit }
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

/* -------------------------
   Shop Images Management
   Upload up to 4 images per shop
   ------------------------- */

/**
 * Get all images for a shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with images array, max_images, can_upload_more
 */
export const getShopImages = (shopId) => {
  return api.get(`/shop/${shopId}/images`, { timeout: 15000 });
};

/**
 * Upload images for a shop (max 4 total)
 * @param {number} shopId - Shop ID
 * @param {FileList|Array} files - Array of image files
 * @returns {Promise} Response with uploaded images and remaining slots
 */
export const uploadShopImages = (shopId, files) => {
  const formData = new FormData();
  for (const file of files) {
    formData.append('images', file);
  }
  return api.post(`/shop/${shopId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  });
};

/**
 * Delete a shop image
 * @param {number} shopId - Shop ID
 * @param {number} imageId - Image ID to delete
 * @returns {Promise} Response with remaining images
 */
export const deleteShopImage = (shopId, imageId) => {
  return api.delete(`/shop/${shopId}/images/${imageId}`, { timeout: 15000 });
};

/**
 * Reorder shop images
 * @param {number} shopId - Shop ID
 * @param {Array<number>} imageIds - Array of image IDs in desired order
 * @returns {Promise} Response with reordered images
 */
export const reorderShopImages = (shopId, imageIds) => {
  return api.put(`/shop/${shopId}/images/reorder`, { image_ids: imageIds }, { timeout: 15000 });
};

/**
 * Set a shop image as the primary/cover image
 * @param {number} shopId - Shop ID
 * @param {number} imageId - Image ID to set as primary
 * @returns {Promise} Response with updated images
 */
export const setShopPrimaryImage = (shopId, imageId) => {
  return api.put(`/shop/${shopId}/images/${imageId}/set-primary`, {}, { timeout: 15000 });
};

export default {
    getShopDashboard,
    uploadSalesData,
    exportSalesData,
    getDistributors,
    getDemandForecast,
    getSalesSummary,
    getQuarterlyForecast,
    getSalesGrowthTrend,
    generateSalesReportPdf,
    getSalesUploadLogs,
    getMyShops,
    createShop,
    updateShop,
    deleteShop,
    downloadSalesTemplate,
    getShopImages,
    uploadShopImages,
    deleteShopImage,
    reorderShopImages,
    setShopPrimaryImage
};
