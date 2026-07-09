import { apiClient } from "@/lib/api/client";
import type { Cart, CartItem } from "@/types/api";

export function getCart(accessToken: string) {
  return apiClient.get<Cart>("/cart/", { token: accessToken });
}

export function addCartItem(
  accessToken: string,
  productId: number,
  quantity: number,
  selectedOptions?: Record<string, number>,
) {
  return apiClient.post<CartItem>(
    "/cart/items/",
    {
      product: productId,
      ...(selectedOptions && Object.keys(selectedOptions).length > 0
        ? { selected_options: selectedOptions }
        : {}),
      quantity,
    },
    { token: accessToken },
  );
}

export function updateCartItem(
  accessToken: string,
  itemId: number,
  quantity: number,
) {
  return apiClient.patch<CartItem>(
    `/cart/items/${itemId}/`,
    { quantity },
    { token: accessToken },
  );
}

export function removeCartItem(accessToken: string, itemId: number) {
  return apiClient.delete<null>(`/cart/items/${itemId}/`, {
    token: accessToken,
  });
}
