import { apiClient } from "@/lib/api/client";
import { trackEvent } from "@/lib/analytics";
import type { Payment } from "@/types/api";

export async function requestPayment(accessToken: string, orderId: number) {
  const payment = await apiClient.post<Payment>(
    "/payments/request/",
    { order_id: orderId },
    { token: accessToken },
  );

  if (payment.payment_url) {
    trackEvent("payment_started", { amount: payment.amount });
  }

  return payment;
}
