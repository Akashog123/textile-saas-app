// src/api/apiMarketing.js
// Marketing caption endpoints powered by inventory selection

import api from './axios';

export const fetchMarketingInventoryProducts = (shopId, params = {}) => {
  return api.get('/marketing/inventory-products', {
    params: { shop_id: shopId, ...params }
  });
};

export const generateInventoryCaptions = (shopId, productIds) => {
  return api.post('/marketing/generate/captions', {
    shop_id: shopId,
    product_ids: productIds
  });
};

export const getMarketingHistory = (params = {}) => {
  return api.get('/marketing/history', { params });
};

export const deleteMarketingHistoryItem = (itemId) => {
  return api.delete(`/marketing/history/${itemId}`);
};

export default {
  fetchMarketingInventoryProducts,
  generateInventoryCaptions,
  getMarketingHistory,
  deleteMarketingHistoryItem
};
