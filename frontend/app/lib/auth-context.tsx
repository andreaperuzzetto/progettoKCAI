"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  fetchMe,
  login as apiLogin,
  register as apiRegister,
  setToken,
  clearToken,
  getToken,
  type UserContext,
  type RestaurantInfo,
} from "./api";

interface AuthContextValue {
  user: UserContext | null;
  activeRestaurant: RestaurantInfo | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  selectRestaurant: (restaurant: RestaurantInfo) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const PUBLIC_PATHS = ["/login", "/register"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserContext | null>(null);
  const [activeRestaurant, setActiveRestaurant] = useState<RestaurantInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const loadUser = useCallback(async () => {
    if (!getToken()) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
      setActiveRestaurant((prev) => {
        if (prev) return prev;
        return me.restaurants[0] ?? null;
      });
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (isLoading) return;
    const isPublic = PUBLIC_PATHS.includes(pathname);
    if (!user && !isPublic) {
      router.push("/login");
    }
    if (user && isPublic) {
      router.push("/");
    }
  }, [user, isLoading, pathname, router]);

  async function login(email: string, password: string) {
    const { access_token } = await apiLogin(email, password);
    setToken(access_token);
    const me = await fetchMe();
    setUser(me);
    setActiveRestaurant(me.restaurants[0] ?? null);
    router.push("/");
  }

  async function register(email: string, password: string) {
    const { access_token } = await apiRegister(email, password);
    setToken(access_token);
    const me = await fetchMe();
    setUser(me);
    setActiveRestaurant(me.restaurants[0] ?? null);
    router.push("/");
  }

  function logout() {
    clearToken();
    setUser(null);
    setActiveRestaurant(null);
    router.push("/login");
  }

  function selectRestaurant(restaurant: RestaurantInfo) {
    setActiveRestaurant(restaurant);
  }

  async function refreshUser() {
    await loadUser();
  }

  return (
    <AuthContext.Provider
      value={{ user, activeRestaurant, isLoading, login, register, logout, selectRestaurant, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
