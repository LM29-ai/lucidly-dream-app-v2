import React, { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { apiClient, setAuthToken } from "../services/api"; // adjust path if needed

interface User {
  id?: string;        // backend may return id
  user_id?: string;   // backend may return user_id
  email: string;
  name: string;
  is_premium?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AUTH_TOKEN_KEY = "authToken";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const setToken = async (newToken: string | null) => {
    setTokenState(newToken);
    setAuthToken(newToken);

    if (newToken) {
      await AsyncStorage.setItem(AUTH_TOKEN_KEY, newToken);
    } else {
      await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
    }
  };

  // Hydrate token + user on app launch
  useEffect(() => {
    (async () => {
      try {
        const savedToken = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
        if (savedToken) {
          setTokenState(savedToken);
          setAuthToken(savedToken);

          // Try to load user
          const meRes = await apiClient.get("/auth/me");
          setUser(meRes.data);
        }
      } catch (e) {
        // If token invalid, clear it
        await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
        setAuthToken(null);
        setTokenState(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      // Your backend currently ignores password; kept for future compatibility
      const res = await apiClient.post("/auth/login", { email, password });
      const newToken = res.data?.token;
      const newUser = res.data?.user;

      if (!newToken || !newUser) {
        throw new Error("Invalid login response from server");
      }

      await setToken(newToken);
      setUser(newUser);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/register", { email, password, name });
      const newToken = res.data?.token;
      const newUser = res.data?.user;

      if (!newToken || !newUser) {
        throw new Error("Invalid register response from server");
      }

      await setToken(newToken);
      setUser(newUser);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      // Optional server-side logout if endpoint exists
      // (safe even if it fails; we still clear locally)
      try {
        await apiClient.post("/auth/logout");
      } catch (_) {}

      setUser(null);
      await setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    if (!token) return;
    const res = await apiClient.get("/auth/me");
    setUser(res.data);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
