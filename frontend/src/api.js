import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

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
