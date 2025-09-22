import axios from 'axios';

const API_BASE_URL = 'https://lucidly-dream-app-v2-production.up.railway.app';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Dream {
  id: string;
  title: string;
  content: string;
  created_at: string;
}