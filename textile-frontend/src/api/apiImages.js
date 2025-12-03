// src/api/apiImages.js

import api from './axios';

/**
 * Compare an image with catalog images to find similar products
 * @param {File} imageFile - The image file to compare
 * @returns {Promise}
 */
export const compareImages = async (imageFile) => {
  const formData = new FormData();
  formData.append('input_image', imageFile);
  
  return api.post('/compare-images/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

export default {
  compareImages
};
