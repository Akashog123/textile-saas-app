// src/api/apiSupplyChain.js
// Supply chain management API endpoints

import api from './axios';

// ============================================================================
// SHOP OWNER ENDPOINTS
// ============================================================================

/**
 * Get all distributors who supply products to shop owner's shops
 * @returns {Promise} Response with suppliers list and summary
 */
export const getShopSuppliers = () => {
    return api.get('/supply-chain/shop/suppliers');
};

/**
 * Get detailed supply records for a specific shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with supply records
 */
export const getShopSupplyDetails = (shopId) => {
    return api.get(`/supply-chain/shop/${shopId}/supply-details`);
};

// ============================================================================
// DISTRIBUTOR ENDPOINTS
// ============================================================================

/**
 * Get all shops this distributor supplies products to
 * @returns {Promise} Response with shops list and summary
 */
export const getSuppliedShops = () => {
    return api.get('/supply-chain/distributor/supplied-shops');
};

/**
 * Get all products this distributor supplies to a specific shop
 * @param {number} shopId - Shop ID
 * @returns {Promise} Response with products list
 */
export const getSuppliedProducts = (shopId) => {
    return api.get(`/supply-chain/distributor/shop/${shopId}/products`);
};

/**
 * Get products that need restocking across all supplied shops
 * @returns {Promise} Response with low stock alerts
 */
export const getLowStockAlerts = () => {
    return api.get('/supply-chain/distributor/low-stock-alerts');
};

export default {
    // Shop owner
    getShopSuppliers,
    getShopSupplyDetails,
    // Distributor
    getSuppliedShops,
    getSuppliedProducts,
    getLowStockAlerts
};
