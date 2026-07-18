import { apiClient } from "@/lib/api/client";
import type { Payment } from "@/types/api";

export function requestPayment(accessToken: string, orderId: number) {
  return apiClient.post<Payment>(
    "/payments/request/",
    { order_id: orderId },
    { token: accessToken },
  );
}
