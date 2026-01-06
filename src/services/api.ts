import axios from "axios";

// IMPORTANT:
// - Set EXPO_PUBLIC_API_BASE_URL in your frontend environment.
// - Example value: https://api.lucidlydreams.com
// - Do NOT include /api at the end; we add it below.

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
  "https://api.lucidlydreams.com";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

// Attach token automatically if present
apiClient.interceptors.request.use(async (config) => {
  // If you store token in AsyncStorage on native and localStorage on web,
  // you can branch here. Keep it simple:
  const token =
    (typeof window !== "undefined" && window.localStorage?.getItem("authToken")) ||
    null;

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Dream {
  id: string;
  title?: string;       // backend may now include it
  content: string;
  created_at: string;
  mood?: string;
  tags?: string[];
  is_public?: boolean;
}
