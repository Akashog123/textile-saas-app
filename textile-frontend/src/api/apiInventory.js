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
 * Download CSV template for inventory import
 * Template columns: name, sku, category, price, purchase_qty, minimum_stock, description, distributor_id
 * @returns {Promise} Response with CSV file blob
 */
export const downloadInventoryTemplate = () => {
    return api.get('/inventory/template/inventory', { responseType: 'blob' });
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
 * @param {FileList|Array} images - Optional image files to upload
 * @returns {Promise} Response with updated product
 */
export const editInventoryItem = (productId, updates, images = null) => {
    if (images && images.length > 0) {
        // Use multipart form data when uploading images
        const formData = new FormData();
        formData.append('product_id', productId);
        
        // Add update fields
        for (const [key, value] of Object.entries(updates)) {
            if (value !== undefined && value !== null) {
                formData.append(key, value);
            }
        }
        
        // Add images
        for (const file of images) {
            formData.append('images', file);
        }
        
        return api.post('/inventory/edit', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000
        });
    }
    
    // Regular JSON request when no images
    return api.post('/inventory/edit', {
        product_id: productId,
        ...updates
    });
};

/**
 * Get all images for a product
 * @param {number} productId - Product ID
 * @returns {Promise} Response with images array
 */
export const getProductImages = (productId) => {
    return api.get(`/inventory/product/${productId}/images`);
};

/**
 * Delete a product image
 * @param {number} productId - Product ID
 * @param {number} imageId - Image ID
 * @returns {Promise} Response with deletion status
 */
export const deleteProductImage = (productId, imageId) => {
    return api.delete(`/inventory/product/${productId}/images/${imageId}`);
};

/**
 * Set a product image as the primary image
 * @param {number} productId - Product ID
 * @param {number} imageId - Image ID
 * @returns {Promise} Response with updated status
 */
export const setProductPrimaryImage = (productId, imageId) => {
    return api.put(`/inventory/product/${productId}/images/${imageId}/set-primary`);
};

/**
 * Delete a product from inventory
 * @param {number} productId - Product ID
 * @returns {Promise} Response with deletion status
 */
export const deleteInventoryItem = (productId) => {
    return api.delete(`/inventory/delete`, { params: { product_id: productId } });
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

/**
 * Bulk upload product images via ZIP file
 * Images should be named by SKU:
 * - Single image: SKU.jpg (e.g., COT-001.jpg)
 * - Multiple images: SKU_1.jpg, SKU_2.jpg (e.g., COT-001_1.jpg, COT-001_2.jpg)
 * 
 * @param {number} shopId - Shop ID
 * @param {File} zipFile - ZIP file containing product images
 * @returns {Promise} Response with upload results
 */
export const bulkUploadProductImages = (shopId, zipFile) => {
    const formData = new FormData();
    formData.append('file', zipFile);
    formData.append('shop_id', shopId);

    return api.post('/inventory/images/bulk-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000 // 2 minutes for large ZIP files
    });
};

export default {
    getInventory,
    importInventory,
    editInventoryItem,
    deleteInventoryItem,
    exportInventory,
    generateInventoryPDF,
    downloadInventoryTemplate,
    getProductImages,
    deleteProductImage,
    setProductPrimaryImage,
    bulkUploadProductImages
};
