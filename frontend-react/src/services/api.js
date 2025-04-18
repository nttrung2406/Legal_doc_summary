import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  signup: async (username, email, password) => {
    const response = await api.post('/signup', {
      username,
      email,
      password,
    });
    return response.data;
  },
};

export const documents = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    

    return response.data;
  },

  list: async () => {
    const response = await api.get('/documents');
    return response.data;
  },

  get: async (filename) => {
    const response = await api.get(`/document/${filename}`);
    return response.data;
  },

  getSummary: async (filename) => {
    const response = await api.post(`/summarize/${filename}`);
    return response.data;
  },

  extractClauses: async (filename) => {
    const response = await api.get(`/clauses/${filename}`);
    return response.data;
  },

  chat: async (filename, query) => {
    const response = await api.post(`/chat/${filename}`, { query });
    return response.data;
  },
};

export default api; 