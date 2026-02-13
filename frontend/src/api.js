import axios from 'axios';

// Use runtime config (for Docker/K8s) or build-time env (for local dev)
const API_URL = window.ENV?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Add token to requests
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (username, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, { username, password });
  if (response.data.access_token) {
    localStorage.setItem('token', response.data.access_token);
  }
  return response.data;
};

export const logout = () => {
    localStorage.removeItem('token');
};

export const getStores = async () => {
  const response = await axios.get(`${API_URL}/stores`);
  return response.data.stores;
};

export const createStore = async (data) => {
  const response = await axios.post(`${API_URL}/stores`, data);
  return response.data;
};

export const deleteStore = async (storeId) => {
  const response = await axios.delete(`${API_URL}/stores/${storeId}`);
  return response.data;
};

export const getCurrentUser = async () => {
    const response = await axios.get(`${API_URL}/users/me`);
    return response.data;
};
