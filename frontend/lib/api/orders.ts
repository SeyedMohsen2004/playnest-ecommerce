import { apiClient } from "@/lib/api/client";
import type { Order } from "@/types/api";

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
