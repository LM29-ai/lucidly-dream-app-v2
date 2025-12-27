import axios from "axios";

const API_BASE_URL = "https://lucidly-dream-app-v2-production.up.railway.app";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export const setAuthToken = (token: string | null) => {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
};

export interface Dream {
  id: string;
  content: string;
  created_at: string;
  mood?: string;
  tags?: string[];
  is_public?: boolean;
  ai_image?: string | null;
  ai_video?: string | null;
  ai_interpretation?: string | null;
}
