import { apiClient } from "@/lib/api/client";
import type {
  CheckoutPayload,
  CheckoutResponse,
  CouponPreviewResponse,
} from "@/types/api";

export function applyCoupon(accessToken: string, code: string) {
  return apiClient.post<CouponPreviewResponse>(
    "/cart/apply-coupon/",
    { code },
    { token: accessToken },
  );
}

export function createCheckoutOrder(
  accessToken: string,
  payload: CheckoutPayload,
) {
  return apiClient.post<CheckoutResponse>("/checkout/", payload, {
    token: accessToken,
  });
}
