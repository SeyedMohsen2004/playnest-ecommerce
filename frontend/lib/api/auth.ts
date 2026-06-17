import { API_BASE_URL, apiClient } from "@/lib/api/client";
import type {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  TokenRefreshResponse,
  User,
  VerifyOtpPayload,
} from "@/types/api";

export type RegisterResponse = {
  message: string;
};

export function registerUser(payload: RegisterPayload) {
  return apiClient.post<RegisterResponse>("/accounts/register/", payload);
}

export function verifyRegisterOtp(payload: VerifyOtpPayload) {
  return apiClient.post<AuthResponse>("/accounts/register/verify/", payload);
}

export function loginUser(payload: LoginPayload) {
  if (process.env.NODE_ENV !== "production") {
    console.log("API base URL:", API_BASE_URL);
    console.log("Login request path:", "/accounts/login/");
    console.log("Login payload keys:", Object.keys(payload));
  }

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
