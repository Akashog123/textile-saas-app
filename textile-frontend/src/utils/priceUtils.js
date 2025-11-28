// Price formatting utilities for consistent display across the app

/**
 * Format price for display - handles various input formats
 * @param {any} priceValue - Price value from backend (could be string, number, or formatted string)
 * @param {string} currency - Currency symbol (default: '₹')
 * @returns {string} - Formatted price string
 */
export const formatPrice = (priceValue, currency = '₹') => {
  if (!priceValue || priceValue === 'N/A' || priceValue === 'NaN' || priceValue === 'nan') {
    return `${currency}N/A`;
  }

  // If it's already a formatted string with currency symbol, return as-is
  if (typeof priceValue === 'string') {
    if (priceValue.includes(currency) || priceValue.includes('$') || priceValue.includes('€')) {
      return priceValue;
    }
    
    // Try to extract numeric value from string
    const numericValue = priceValue.replace(/[^\d.]/g, '');
    const parsedValue = parseFloat(numericValue);
    
    if (isNaN(parsedValue)) {
      return `${currency}N/A`;
    }
    
    return `${currency}${parsedValue.toLocaleString()}`;
  }

  // If it's a number, format it
  if (typeof priceValue === 'number') {
    return `${currency}${priceValue.toLocaleString()}`;
  }

  // Fallback
  return `${currency}N/A`;
};

/**
 * Extract numeric value from price string for calculations
 * @param {any} priceValue - Price value from backend
 * @returns {number} - Numeric value or 0 if invalid
 */
export const extractNumericPrice = (priceValue) => {
  if (!priceValue || priceValue === 'N/A') {
    return 0;
  }

  if (typeof priceValue === 'number') {
    return priceValue;
  }

  if (typeof priceValue === 'string') {
    // Remove all non-numeric characters except decimal point
    const numericValue = priceValue.replace(/[^\d.]/g, '');
    const parsedValue = parseFloat(numericValue);
    return isNaN(parsedValue) ? 0 : parsedValue;
  }

  return 0;
};

/**
 * Format price per meter specifically
 * @param {any} priceValue - Price value from backend
 * @param {string} currency - Currency symbol (default: '₹')
 * @returns {string} - Formatted price per meter
 */
export const formatPricePerMeter = (priceValue, currency = '₹') => {
  const formattedPrice = formatPrice(priceValue, currency);
  return formattedPrice === `${currency}N/A` ? 'Price not available' : `${formattedPrice}`;
};

export default {
  formatPrice,
  extractNumericPrice,
  formatPricePerMeter
};
