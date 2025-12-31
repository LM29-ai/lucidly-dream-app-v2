import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

const BASE = process.env.EXPO_PUBLIC_API_URL;

if (!BASE) {
  console.warn("Missing EXPO_PUBLIC_API_URL in .env");
}

export const apiClient = axios.create({
  baseURL: `${BASE}/api`,
  headers: { "Content-Type": "application/json" }
});

apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("authToken");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
