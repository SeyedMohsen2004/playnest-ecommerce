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

import {
  getCurrentUser,
  loginUser,
  logoutUser,
  refreshSession,
  registerUser,
  resendRegistration,
  verifyRegistration,
} from "@/lib/api/auth";
import { getFriendlyApiError } from "@/lib/api/errors";
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
  register: (payload: RegisterPayload) => Promise<void>;
  verifyRegistration: (payload: VerifyRegistrationPayload) => Promise<void>;
  resendRegistration: (
    payload: ResendRegistrationPayload,
  ) => Promise<PendingRegistrationResponse>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function getFriendlyAuthError(
  error: unknown,
  fallback = "در ارتباط با سرور مشکلی پیش آمد. کمی بعد دوباره تلاش کنید.",
) {
  return getFriendlyApiError(error, fallback);
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

  const register = useCallback(async (payload: RegisterPayload) => {
    const response = await registerUser(payload);
    replaceSessionAccessToken(response.access);
    setUser(response.user);
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
