import { apiClient, refreshSession } from "@/lib/api/client";
import type {
  AuthResponse,
  LoginPayload,
  PendingRegistrationResponse,
  RegisterPayload,
  ResendRegistrationPayload,
  User,
  VerifyRegistrationPayload,
} from "@/types/api";

const cookieMutationOptions = {
  credentials: "include" as const,
  csrf: true,
  retryAuth: false,
};

export function registerUser(payload: RegisterPayload) {
  return apiClient.post<PendingRegistrationResponse>(
    "/accounts/register/",
    payload,
    cookieMutationOptions,
  );
}

export function verifyRegistration(payload: VerifyRegistrationPayload) {
  return apiClient.post<AuthResponse>(
    "/accounts/register/verify/",
    payload,
    cookieMutationOptions,
  );
}

export function resendRegistration(payload: ResendRegistrationPayload) {
  return apiClient.post<PendingRegistrationResponse>(
    "/accounts/register/resend/",
    payload,
    cookieMutationOptions,
  );
}

export function loginUser(payload: LoginPayload) {
  return apiClient.post<AuthResponse>(
    "/accounts/login/",
    payload,
    cookieMutationOptions,
  );
}

export function logoutUser() {
  return apiClient.post<{ message: string }>(
    "/accounts/logout/",
    undefined,
    cookieMutationOptions,
  );
}

export function getCurrentUser(accessToken: string) {
  return apiClient.get<User>("/accounts/me/", { token: accessToken });
}

export { refreshSession };
