import { apiClient } from "@/lib/api/client";
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  TokenRefreshResponse,
  User,
} from "@/types/api";

export function registerUser(payload: RegisterPayload) {
  return apiClient.post<AuthResponse>("/accounts/register/", payload);
}

export function loginUser(payload: LoginPayload) {
  return apiClient.post<AuthResponse>("/accounts/login/", payload);
}

export function getCurrentUser(accessToken: string) {
  return apiClient.get<User>("/accounts/me/", { token: accessToken });
}

export function refreshToken(refreshTokenValue: string) {
  return apiClient.post<TokenRefreshResponse>("/auth/token/refresh/", {
    refresh: refreshTokenValue,
  });
}
