import { apiClient } from "@/lib/api/client";
import type { ShippingRatesResponse } from "@/types/api";

export function getShippingRates() {
  return apiClient.get<ShippingRatesResponse>("/shipping-rates/");
}
