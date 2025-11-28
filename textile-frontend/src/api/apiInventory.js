// src/api/apiInventory.js
// Inventory management API endpoints

import api from './axios';

/**
 * Get inventory for a shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with inventory products
 */
export const getInventory = (shopId) => {
    return api.get(`/inventory/`, { params: { shop_id: shopId } });
};

/**
 * Import inventory from CSV/Excel file
 * @param {number} shopId - Shop ID
 * @param {File} file - CSV or Excel file with product data
 * @returns {Promise} Response with import status
 */
export const importInventory = (shopId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('shop_id', shopId);

    return api.post('/inventory/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
    });
};

/**
 * Edit/update a product in inventory
 * @param {number} productId - Product ID
 * @param {Object} updates - Fields to update (price, stock, etc.)
 * @returns {Promise} Response with updated product
 */
export const editInventoryItem = (productId, updates) => {
    return api.post('/inventory/edit', {
        product_id: productId,
        ...updates
    });
};

/**
 * Delete a product from inventory
 * @param {number} productId - Product ID
 * @returns {Promise} Response with deletion status
 */
export const deleteInventoryItem = (productId) => {
    return api.delete(`/inventory/delete`, { data: { product_id: productId } });
};

/**
 * Generate detailed PDF report for inventory
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with PDF file blob
 */
export const generateInventoryPDF = (shopId) => {
    return api.get(`/inventory/report/pdf`, {
        params: { shop_id: shopId },
        responseType: 'blob'
    });
};

/**
 * Export inventory as Excel file
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with file blob
 */
export const exportInventory = (shopId) => {
    return api.get(`/inventory/export`, {
        params: { shop_id: shopId },
        responseType: 'blob'
    });
};

export default {
    getInventory,
    importInventory,
    editInventoryItem,
    deleteInventoryItem,
    exportInventory,
    generateInventoryPDF
};
