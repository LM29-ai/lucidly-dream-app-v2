import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { apiClient } from "../services/api";

type User = { id: string; email: string; name: string; is_premium?: boolean };

type AuthContextType = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function bootstrap() {
    try {
      const savedToken = await AsyncStorage.getItem("authToken");
      if (savedToken) {
        setToken(savedToken);
        const me = await apiClient.get("/auth/me");
        if (me.data?.id) setUser(me.data);
      }
    } catch {
      // token invalid, clear it
      await AsyncStorage.removeItem("authToken");
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    bootstrap();
  }, []);

  async function login(email: string, password: string) {
    const res = await apiClient.post("/auth/login", { email, password });
    const t = res.data?.token;
    const u = res.data?.user;
    if (!t || !u) throw new Error("Login failed: missing token/user");

    await AsyncStorage.setItem("authToken", t);
    setToken(t);
    setUser(u);
  }

  async function register(email: string, password: string, name: string) {
    const res = await apiClient.post("/auth/register", { email, password, name });
    const t = res.data?.token;
    const u = res.data?.user;
    if (!t || !u) throw new Error("Register failed: missing token/user");

    await AsyncStorage.setItem("authToken", t);
    setToken(t);
    setUser(u);
  }

  async function logout() {
    try {
      // Optional if backend supports it:
      await apiClient.post("/auth/logout");
    } catch {
      // ignore
    }
    await AsyncStorage.removeItem("authToken");
    setToken(null);
    setUser(null);
  }

  async function refreshUser() {
    const me = await apiClient.get("/auth/me");
    if (me.data?.id) setUser(me.data);
  }

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout, refreshUser }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
