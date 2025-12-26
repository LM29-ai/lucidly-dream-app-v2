import axios from "axios";

// Your Railway backend root (no /api at end)
const API_BASE_URL = "https://lucidly-dream-app-v2-production.up.railway.app";

// We'll set the token from AuthContext via setAuthToken()
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 20000,
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
  mood: string;
  tags: string[];
  created_at: string;
  ai_image?: string | null;
  ai_video?: string | null;
  ai_interpretation?: string | null;
}
