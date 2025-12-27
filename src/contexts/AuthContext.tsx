import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { apiClient, setAuthToken } from "../services/api";

interface User {
  id: string;
  email: string;
  name: string;
  is_premium?: boolean;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
  refreshing: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

const TOKEN_KEY = "authToken";

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(true);

  // Load token on app start
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(TOKEN_KEY);
        if (stored) {
          setToken(stored);
          setAuthToken(stored);
          await refreshUser(stored);
        }
      } finally {
        setRefreshing(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshUser = async (overrideToken?: string) => {
    const t = overrideToken ?? token;
    if (!t) return;

    try {
      setAuthToken(t);
      const res = await apiClient.get("/auth/me");
      setUser(res.data);
    } catch (e) {
      // Token invalid/expired → hard reset
      await AsyncStorage.removeItem(TOKEN_KEY);
      setAuthToken(null);
      setToken(null);
      setUser(null);
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/login", { email, password });
      const t = res.data?.token;
      const u = res.data?.user;

      if (!t || !u) throw new Error("Missing token/user from backend");

      await AsyncStorage.setItem(TOKEN_KEY, t);
      setAuthToken(t);
      setToken(t);
      setUser(u);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/register", { email, password, name });
      const t = res.data?.token;
      const u = res.data?.user;

      if (!t || !u) throw new Error("Missing token/user from backend");

      await AsyncStorage.setItem(TOKEN_KEY, t);
      setAuthToken(t);
      setToken(t);
      setUser(u);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // tell backend to invalidate session too (important)
      await apiClient.post("/auth/logout");
    } catch {
      // ignore
    }
    await AsyncStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        loading,
        refreshing,
        refreshUser: () => refreshUser(),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

