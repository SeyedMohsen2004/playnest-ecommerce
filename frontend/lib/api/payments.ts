import { APIError, apiClient } from "@/lib/api/client";
import type {
  PaymentRequestResponse,
  PaymentVerifyResponse,
} from "@/types/api";

export async function requestPayment(accessToken: string, orderId: number) {
  try {
    return await apiClient.post<PaymentRequestResponse>(
      "/payments/request/",
      { order: orderId },
      { token: accessToken },
    );
  } catch (error) {
    if (error instanceof APIError && error.status === 400) {
      return apiClient.post<PaymentRequestResponse>(
        "/payments/request/",
        { order_id: orderId },
        { token: accessToken },
      );
    }

    throw error;
  }
}

export function verifyPayment(
  accessToken: string,
  authority: string,
  status: "OK" | "NOK" = "OK",
) {
  return apiClient.post<PaymentVerifyResponse>(
    "/payments/verify/",
    {
      authority,
      status,
    },
    { token: accessToken },
  );
}
