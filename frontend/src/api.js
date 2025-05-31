import axios from "axios";
import { ACCESS_TOKEN } from "./constants";

const apiUrl = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : "http://localhost:8000";

const api = axios.create({
  baseURL: apiUrl,
  timeout: 10000, // 10 segundos timeout
  headers: {
    'Content-Type': 'application/json',
  }
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_TOKEN);
    console.log('🔐 Axios Interceptor - Token found:', !!token);
    console.log('🔗 Request URL:', config.url);
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Authorization header set');
    } else {
      console.log('❌ No token found in localStorage');
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Axios request interceptor error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error(`❌ API Error: ${error.response.status} - ${error.response.config.url}`);
      console.error('Error details:', error.response.data);
    } else {
      console.error('❌ Network/Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
