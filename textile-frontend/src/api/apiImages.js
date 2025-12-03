// src/api/apiImages.js
// Deprecated - use searchByImage from apiCustomer.js instead

import api from './axios';

/**
 * @deprecated Use searchByImage from apiCustomer.js instead
 * Compare an image with catalog images to find similar products
 * @param {File} imageFile - The image file to compare
 * @returns {Promise}
 */
export const compareImages = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('limit', 20);
  
  return api.post('/image-search/similar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 15000
  });
};

export default {
  compareImages
};
