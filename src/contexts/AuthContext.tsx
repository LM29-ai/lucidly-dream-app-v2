import React, { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { apiClient, setAuthToken } from "./api"; // adjust path if needed

interface User {
  id: string;
  email: string;
  name: string;
  is_premium?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
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
  const [token, setTokenState] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const setToken = async (newToken: string | null) => {
    setTokenState(newToken);
    setAuthToken(newToken);
    if (newToken) {
      await AsyncStorage.setItem(TOKEN_KEY, newToken);
    } else {
      await AsyncStorage.removeItem(TOKEN_KEY);
    }
  };

  const refreshUser = async () => {
    if (!token) return;
    try {
      const res = await apiClient.get("/auth/me");
      if (res?.data?.error) throw new Error(res.data.error);
      setUser(res.data);
    } catch (e) {
      // token invalid → force logout
      await logout();
    }
  };

  // Boot: load saved token and fetch user
  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem(TOKEN_KEY);
        if (saved) {
          setTokenState(saved);
          setAuthToken(saved);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // After token set, fetch user
  useEffect(() => {
    if (token) refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/login", { email, password });
      if (res?.data?.error) throw new Error(res.data.error);

      await setToken(res.data.token);
      setUser(res.data.user);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/register", { email, password, name });
      if (res?.data?.error) throw new Error(res.data.error);

      await setToken(res.data.token);
      setUser(res.data.user);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setUser(null);
    await setToken(null);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      login,
      register,
      logout,
      loading,
      refreshUser,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
