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
  logoutUser,
  refreshSession,
  registerUser,
  resendRegistration,
  verifyRegistration,
} from "@/lib/api/auth";
import {
  getSessionGeneration,
  invalidateSession,
  purgeLegacyBrowserTokens,
  replaceSessionAccessToken,
  subscribeToSessionInvalidation,
} from "@/lib/auth/token-storage";
import type {
  LoginPayload,
  PendingRegistrationResponse,
  RegisterPayload,
  ResendRegistrationPayload,
  User,
  VerifyRegistrationPayload,
} from "@/types/api";

type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<PendingRegistrationResponse>;
  verifyRegistration: (payload: VerifyRegistrationPayload) => Promise<void>;
  resendRegistration: (
    payload: ResendRegistrationPayload,
  ) => Promise<PendingRegistrationResponse>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function extractErrorText(data: unknown): string | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const record = data as Record<string, unknown>;
  const preferredKeys = ["detail", "message", "non_field_errors", "code"];

  for (const key of preferredKeys) {
    const value = record[key];
    if (typeof value === "string") return value;
    if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  }

  const firstValue = Object.values(record)[0];
  if (typeof firstValue === "string") return firstValue;
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
    return "ارتباط با سرور برقرار نشد. لطفاً کمی بعد دوباره تلاش کنید.";
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    purgeLegacyBrowserTokens();

    const unsubscribe = subscribeToSessionInvalidation(() => {
      if (isMounted) setUser(null);
    });

    async function hydrateSession() {
      const hydrationGeneration = getSessionGeneration();
      try {
        const access = await refreshSession();
        const currentUser = await getCurrentUser(access);
        if (
          isMounted &&
          hydrationGeneration === getSessionGeneration()
        ) {
          setUser(currentUser);
        }
      } catch {
        if (
          isMounted &&
          hydrationGeneration === getSessionGeneration()
        ) {
          setUser(null);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    hydrateSession();
    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await loginUser(payload);
    replaceSessionAccessToken(response.access);
    setUser(response.user);
  }, []);

  const register = useCallback((payload: RegisterPayload) => {
    return registerUser(payload);
  }, []);

  const verify = useCallback(async (payload: VerifyRegistrationPayload) => {
    const response = await verifyRegistration(payload);
    replaceSessionAccessToken(response.access);
    setUser(response.user);
  }, []);

  const resend = useCallback((payload: ResendRegistrationPayload) => {
    return resendRegistration(payload);
  }, []);

  const logout = useCallback(async () => {
    invalidateSession();
    try {
      await logoutUser();
    } catch {
      // Local invalidation is authoritative; the short-lived access token is gone
      // and the server-side refresh cookie will be retried/cleared on a later visit.
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      register,
      verifyRegistration: verify,
      resendRegistration: resend,
      logout,
    }),
    [isLoading, login, logout, register, resend, user, verify],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
