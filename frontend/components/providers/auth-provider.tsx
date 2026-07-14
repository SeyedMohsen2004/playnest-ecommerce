"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { APIError } from "@/lib/api/client";
import {
  getCurrentUser,
  loginUser,
  refreshToken as requestTokenRefresh,
  registerUser,
} from "@/lib/api/auth";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "@/lib/auth/token-storage";
import type {
  LoginPayload,
  RegisterPayload,
  User,
} from "@/types/api";

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function extractErrorText(data: unknown): string | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const record = data as Record<string, unknown>;
  const preferredKeys = ["detail", "message", "non_field_errors", "phone_number"];

  for (const key of preferredKeys) {
    const value = record[key];

    if (typeof value === "string") {
      return value;
    }

    if (Array.isArray(value) && typeof value[0] === "string") {
      return value[0];
    }
  }

  const firstValue = Object.values(record)[0];

  if (typeof firstValue === "string") {
    return firstValue;
  }

  if (Array.isArray(firstValue) && typeof firstValue[0] === "string") {
    return firstValue[0];
  }

  return null;
}

export function getFriendlyAuthError(
  error: unknown,
  fallback = "در ارتباط با سرور مشکلی پیش آمد. کمی بعد دوباره تلاش کنید.",
) {
  if (error instanceof APIError) {
    return extractErrorText(error.data) || error.message || fallback;
  }

  if (error instanceof TypeError) {
    return "ارتباط با سرور برقرار نشد. لطفا اجرای بک‌اند و تنظیمات CORS را بررسی کنید.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      const accessToken = getAccessToken();
      const storedRefreshToken = getRefreshToken();

      if (!accessToken && !storedRefreshToken) {
        setIsLoading(false);
        return;
      }

      try {
        if (accessToken) {
          try {
            const currentUser = await getCurrentUser(accessToken);

            if (isMounted) {
              setUser(currentUser);
            }

            return;
          } catch {
            if (!storedRefreshToken) {
              throw new Error("Stored access token is no longer valid.");
            }
          }
        }

        if (storedRefreshToken) {
          const refreshed = await requestTokenRefresh(storedRefreshToken);
          setTokens({
            access: refreshed.access,
            refresh: storedRefreshToken,
          });
          const currentUser = await getCurrentUser(refreshed.access);

          if (isMounted) {
            setUser(currentUser);
          }
        }
      } catch {
        clearTokens();

        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await loginUser(payload);
    setTokens(response);
    setUser(response.user);
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const response = await registerUser(payload);
    setTokens(response);
    setUser(response.user);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      register,
      logout,
    }),
    [isLoading, login, logout, register, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
