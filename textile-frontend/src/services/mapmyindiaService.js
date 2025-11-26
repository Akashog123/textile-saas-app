/**
 * MapmyIndia Service
 * Handles geolocation and nearby shop search using MapmyIndia API
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * Get user's current geolocation
 * @returns {Promise<{latitude: number, longitude: number}>}
 */
export const getUserLocation = () => {
    return new Promise((resolve, reject) => {
        if (!('geolocation' in navigator)) {
            reject(new Error('Geolocation is not supported by your browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            (error) => {
                let errorMessage = 'Failed to get location';

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location permission denied. Please enable location access in your browser settings.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable. Please check your GPS settings.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out. Please try again.';
                        break;
                    default:
                        errorMessage = 'An unknown error occurred while getting location.';
                }

                reject(new Error(errorMessage));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000, // 10 seconds
                maximumAge: 60000 // Accept cached position up to 1 minute old
            }
        );
    });
};

/**
 * Search for nearby shops using MapmyIndia API via our backend proxy
 * @param {number} latitude - User's latitude
 * @param {number} longitude - User's longitude
 * @param {number} radius - Search radius in meters (default: 5000)
 * @param {string} keywords - Search keywords (default: "textile shop;fabric shop")
 * @returns {Promise<{shops: Array, user_location: Object, total_results: number}>}
 */
export const searchNearbyShops = async (latitude, longitude, radius = 5000, keywords = 'textile shop;fabric shop;cloth shop') => {
    try {
        const response = await axios.post(`${API_BASE_URL}/api/nearby-shops`, {
            latitude,
            longitude,
            radius,
            keywords
        });

        if (response.data.success) {
            return response.data.data;
        } else {
            throw new Error(response.data.error || 'Failed to search nearby shops');
        }
    } catch (error) {
        if (error.response) {
            // Server responded with error status
            const errorMsg = error.response.data?.error || 'Server error occurred';
            throw new Error(errorMsg);
        } else if (error.request) {
            // Request was made but no response received
            throw new Error('No response from server. Please check your internet connection.');
        } else {
            // Something else went wrong
            throw new Error(error.message || 'An error occurred while searching nearby shops');
        }
    }
};

/**
 * Get nearby shops with automatic geolocation
 * Combines getUserLocation and searchNearbyShops
 * @param {number} radius - Search radius in meters (default: 5000)
 * @param {string} keywords - Search keywords
 * @returns {Promise<{shops: Array, user_location: Object, total_results: number}>}
 */
export const getNearbyShopsAuto = async (radius = 5000, keywords = 'textile shop;fabric shop;cloth shop') => {
    try {
        // Get user's location
        const location = await getUserLocation();

        // Search nearby shops
        const result = await searchNearbyShops(
            location.latitude,
            location.longitude,
            radius,
            keywords
        );

        return result;
    } catch (error) {
        throw error;
    }
};

/**
 * Calculate distance between two coordinates (Haversine formula)
 * @param {number} lat1 - First point latitude
 * @param {number} lon1 - First point longitude
 * @param {number} lat2 - Second point latitude  
 * @param {number} lon2 - Second point longitude
 * @returns {number} Distance in meters
 */
export const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δφ = ((lat2 - lat1) * Math.PI) / 180;
    const Δλ = ((lon2 - lon1) * Math.PI) / 180;

    const a =
        Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
};

/**
 * Format distance for display
 * @param {number} meters - Distance in meters
 * @returns {string} Formatted distance string
 */
export const formatDistance = (meters) => {
    if (meters < 1000) {
        return `${Math.round(meters)}m`;
    } else {
        return `${(meters / 1000).toFixed(1)}km`;
    }
};

/**
 * Check if geolocation is available
 * @returns {boolean}
 */
export const isGeolocationAvailable = () => {
    return 'geolocation' in navigator;
};

export default {
    getUserLocation,
    searchNearbyShops,
    getNearbyShopsAuto,
    calculateDistance,
    formatDistance,
    isGeolocationAvailable
};
