// src/api/apiAuth.js
// Authentication and session management API endpoints

import api from './axios';

/**
 * User login with username/email and password
 * @param {string} username - Username or email
 * @param {string} password - User password
 * @returns {Promise} Response with JWT token and user profile
 */
export const login = (username, password) => {
    return api.post('/auth/login', { username, password });
};

/**
 * User logout (clears session on server)
 * @returns {Promise} Response acknowledging logout
 */
export const logout = () => {
    return api.post('/auth/logout');
};

/**
 * Register new user account
 * @param {Object} userData - User registration data
 * @param {string} userData.username - Unique username
 * @param {string} userData.email - Email address
 * @param {string} userData.password - Password
 * @param {string} userData.role - User role (customer, shop_owner, distributor)
 * @param {Object} userData.profile - Additional profile data
 * @returns {Promise} Response with created user profile
 */
export const register = (userData) => {
    return api.post('/auth/register', userData);
};

/**
 * Get current authenticated user session
 * @returns {Promise} Response with current user profile
 */
export const getCurrentSession = () => {
    return api.get('/auth/session');
};

/**
 * Verify JWT token validity
 * @param {string} token - JWT token to verify
 * @returns {Promise} Response with token validation result
 */
export const verifyToken = (token) => {
    return api.post('/auth/verify_token', { token });
};

/**
 * Refresh authentication token
 * @returns {Promise} Response with new JWT token
 */
export const refreshToken = () => {
    return api.post('/auth/refresh_token');
};

export default {
    login,
    logout,
    register,
    getCurrentSession,
    verifyToken,
    refreshToken
};
