import axios from 'axios';

// Verisca Web uses the production API
const API_BASE_URL = 'https://verisca.onrender.com/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    async (config) => {
        // Check localStorage (since this is web)
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('verisca_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Auto-logout on 401
            if (typeof window !== 'undefined') {
                localStorage.removeItem('verisca_token');
                window.location.href = '/';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
