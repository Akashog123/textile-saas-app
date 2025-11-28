/**
 * Comprehensive error handling utilities for frontend-backend consistency
 * Provides graceful fallbacks and user-friendly error messages
 */

/**
 * Handle API response errors with user-friendly messages
 * @param {Error} error - Error object from API call
 * @param {string} context - Context of the error (e.g., 'products', 'shops')
 * @returns {string} - User-friendly error message
 */
export const handleApiError = (error, context = 'API') => {
  console.error(`[${context}] Error:`, error);
  
  // Network errors
  if (!navigator.onLine) {
    return 'You are offline. Please check your internet connection.';
  }
  
  // Axios/network errors
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }
  
  if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
    return 'Network connection failed. Please check your internet connection.';
  }
  
  // HTTP status errors
  if (error.response) {
    const status = error.response.status;
    const message = error.response.data?.message || '';
    
    switch (status) {
      case 400:
        return message || 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You do not have permission to access this resource.';
      case 404:
        return 'The requested information was not found.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error. Our team has been notified. Please try again later.';
      case 502:
      case 503:
      case 504:
        return 'Service temporarily unavailable. Please try again in a few minutes.';
      default:
        return message || `Request failed with status ${status}. Please try again.`;
    }
  }
  
  // Client-side errors
  if (error.message) {
    if (error.message.includes('Failed to fetch')) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }
    return error.message;
  }
  
  // Unknown errors
  return 'An unexpected error occurred. Please try again.';
};

/**
 * Handle data parsing errors with fallback
 * @param {*} data - Data to validate
 * @param {string} dataType - Type of data (e.g., 'product', 'shop')
 * @param {Object} fallback - Fallback data object
 * @returns {Object} - Validated data or fallback
 */
export const handleDataError = (data, dataType, fallback) => {
  if (!data || typeof data !== 'object') {
    console.warn(`[${dataType}] Invalid data received, using fallback`);
    return fallback;
  }
  
  // Check for required fields based on data type
  const requiredFields = getRequiredFields(dataType);
  const missingFields = requiredFields.filter(field => !(field in data));
  
  if (missingFields.length > 0) {
    console.warn(`[${dataType}] Missing required fields: ${missingFields.join(', ')}`);
    return fallback;
  }
  
  return data;
};

/**
 * Get required fields for different data types
 * @param {string} dataType - Type of data
 * @returns {Array} - Array of required field names
 */
const getRequiredFields = (dataType) => {
  switch (dataType.toLowerCase()) {
    case 'product':
      return ['id', 'name'];
    case 'shop':
      return ['id', 'name'];
    case 'fabric':
      return ['id', 'name'];
    case 'user':
      return ['id', 'username'];
    default:
      return ['id'];
  }
};

/**
 * Create retry configuration for failed requests
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} delay - Delay between retries in ms
 * @returns {Object} - Retry configuration
 */
export const createRetryConfig = (maxRetries = 3, delay = 1000) => ({
  maxRetries,
  delay,
  retryDelay: (retryCount) => delay * Math.pow(2, retryCount), // Exponential backoff
  retryCondition: (error) => {
    // Retry on network errors and 5xx server errors
    return !error.response || (error.response.status >= 500 && error.response.status < 600);
  }
});

/**
 * Execute API call with retry logic
 * @param {Function} apiCall - API function to call
 * @param {Object} retryConfig - Retry configuration
 * @returns {Promise} - API response
 */
export const executeWithRetry = async (apiCall, retryConfig = createRetryConfig()) => {
  let lastError;
  
  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      const response = await apiCall();
      return response;
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx) or if this is the last attempt
      if (attempt === retryConfig.maxRetries || !retryConfig.retryCondition(error)) {
        throw error;
      }
      
      // Wait before retrying
      await new Promise(resolve => 
        setTimeout(resolve, retryConfig.retryDelay(attempt))
      );
      
      console.warn(`Retrying API call (attempt ${attempt + 1}/${retryConfig.maxRetries})`);
    }
  }
  
  throw lastError;
};

/**
 * Log errors for debugging and monitoring
 * @param {Error} error - Error object
 * @param {string} context - Context of the error
 * @param {Object} additionalInfo - Additional information to log
 */
export const logError = (error, context, additionalInfo = {}) => {
  const errorData = {
    timestamp: new Date().toISOString(),
    context,
    message: error.message,
    stack: error.stack,
    response: error.response?.data,
    status: error.response?.status,
    ...additionalInfo
  };
  
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('[Error Log]', errorData);
  }
  
  // In production, you might want to send this to a logging service
  // For now, we'll just store in localStorage for debugging
  try {
    const errorLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
    errorLogs.push(errorData);
    
    // Keep only last 50 errors to prevent localStorage bloat
    if (errorLogs.length > 50) {
      errorLogs.splice(0, errorLogs.length - 50);
    }
    
    localStorage.setItem('errorLogs', JSON.stringify(errorLogs));
  } catch (e) {
    console.warn('Failed to log error to localStorage:', e);
  }
};

/**
 * Get recent error logs for debugging
 * @param {number} limit - Maximum number of errors to return
 * @returns {Array} - Array of error logs
 */
export const getErrorLogs = (limit = 10) => {
  try {
    const errorLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
    return errorLogs.slice(-limit);
  } catch (e) {
    console.warn('Failed to retrieve error logs:', e);
    return [];
  }
};

/**
 * Clear error logs
 */
export const clearErrorLogs = () => {
  try {
    localStorage.removeItem('errorLogs');
  } catch (e) {
    console.warn('Failed to clear error logs:', e);
  }
};

/**
 * Show user-friendly notification for errors
 * @param {string} message - Error message to show
 * @param {string} type - Type of notification ('error', 'warning', 'info')
 * @param {number} duration - Duration in ms to show notification
 */
export const showErrorNotification = (message, type = 'error', duration = 5000) => {
  // Create notification element if it doesn't exist
  let notification = document.getElementById('error-notification');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'error-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      max-width: 400px;
      padding: 15px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;
    document.body.appendChild(notification);
  }
  
  // Set styling based on type
  const colors = {
    error: 'linear-gradient(135deg, #f56565, #e53e3e)',
    warning: 'linear-gradient(135deg, #ed8936, #dd6b20)',
    info: 'linear-gradient(135deg, #4299e1, #3182ce)'
  };
  
  notification.style.background = colors[type] || colors.error;
  notification.textContent = message;
  
  // Show notification
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 100);
  
  // Hide notification after duration
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
  }, duration);
};

export default {
  handleApiError,
  handleDataError,
  createRetryConfig,
  executeWithRetry,
  logError,
  getErrorLogs,
  clearErrorLogs,
  showErrorNotification
};
