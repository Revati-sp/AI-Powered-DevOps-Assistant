"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { fetchCurrentUser, logoutRequest, type UserResponse } from "@/features/auth/api";

const LOGOUT_STORAGE_KEY = "ada-logout";

export type AuthContextValue = {
  user: UserResponse | null;
  isLoading: boolean;
  refreshUser: () => Promise<UserResponse | null>;
  logout: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = React.useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const refreshUser = React.useCallback(async () => {
    try {
      const next = await fetchCurrentUser();
      setUser(next);
      return next;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    (async () => {
      setIsLoading(true);
      try {
        const next = await fetchCurrentUser();
        if (!cancelled) {
          setUser(next);
        }
      } catch {
        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === LOGOUT_STORAGE_KEY) {
        setUser(null);
        router.replace("/login");
      }
    };

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [router]);

  const logout = React.useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // Clear local auth state even if the network call fails.
    } finally {
      setUser(null);
      try {
        localStorage.setItem(LOGOUT_STORAGE_KEY, String(Date.now()));
      } catch {
        // Ignore storage quota / private mode failures.
      }
      router.replace("/login");
    }
  }, [router]);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      refreshUser,
      logout,
    }),
    [user, isLoading, refreshUser, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
