import { apiClient } from "@/lib/api/client";
import type { Order, OrderShippingPayload } from "@/types/api";

export function getOrders(accessToken: string) {
  return apiClient.get<Order[]>("/orders/", { token: accessToken });
}

export function getOrder(accessToken: string, orderId: number) {
  return apiClient.get<Order>(`/orders/${orderId}/`, { token: accessToken });
}

export function cancelOrder(accessToken: string, orderId: number) {
  return apiClient.post<Order>(
    `/orders/${orderId}/cancel/`,
    {},
    { token: accessToken },
  );
}

export function updateOrderShipping(
  accessToken: string,
  orderId: number,
  payload: OrderShippingPayload,
) {
  return apiClient.patch<Order>(`/orders/${orderId}/shipping/`, payload, {
    token: accessToken,
  });
}
