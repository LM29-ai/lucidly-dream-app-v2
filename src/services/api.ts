import axios from "axios";

const API_BASE_URL = "https://lucidly-dream-app-v2-production.up.railway.app";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

let currentToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  currentToken = token;
};

// Attach Authorization header on every request
apiClient.interceptors.request.use((config) => {
  if (currentToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${currentToken}`;
  }
  return config;
});

// Optional: if 401, you can handle global logout in UI logic
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    return Promise.reject(err);
  }
);

export interface Dream {
  id: string;
  title: string;
  content: string;
  created_at: string;
  mood?: string;
  tags?: string[];
  is_public?: boolean;
}

