import axios from 'axios';

// Get API URL from environment variables or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base URL
const instance = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor - could be used for authentication tokens later
instance.interceptors.request.use(
  (config) => {
    // You can modify the request config here (add authentication headers, etc.)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
instance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle global error responses here
    console.error('API Error:', error);
    
    // Check if it's a network error
    if (!error.response) {
      console.error('Network Error - Backend may be offline');
    }
    
    return Promise.reject(error);
  }
);

export default instance; 