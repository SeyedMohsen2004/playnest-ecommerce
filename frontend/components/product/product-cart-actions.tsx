"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { QuantitySelector } from "@/components/shared/quantity-selector";
import { Button } from "@/components/ui/button";
import { addCartItem } from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { getCartErrorMessage, getStockLimitMessage } from "@/lib/api/errors";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";

type ProductCartActionsProps = {
  productId: number | null;
  isInStock: boolean;
  availableStock?: number | null;
  selectedOptions?: Record<string, number>;
  requiresOptions?: boolean;
  optionMessage?: string;
};

export function ProductCartActions({
  productId,
  isInStock,
  availableStock,
  selectedOptions = {},
  requiresOptions = false,
  optionMessage = "",
}: ProductCartActionsProps) {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"success" | "error">(
    "success",
  );
  const normalizedAvailableStock =
    typeof availableStock === "number" && Number.isFinite(availableStock)
      ? Math.max(0, Math.floor(availableStock))
      : null;

  async function handleAddToCart() {
    setMessage("");

    if (!isAuthenticated) {
      setMessageTone("error");
      setMessage("برای افزودن محصول به سبد خرید ابتدا وارد شوید.");
      router.push("/login");
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      logout();
      router.push("/login");
      return;
    }

    if (typeof productId !== "number" || !Number.isFinite(productId)) {
      setMessageTone("error");
      setMessage("این محصول فعلا امکان افزودن به سبد خرید ندارد.");
      return;
    }

    if (requiresOptions && optionMessage) {
      setMessageTone("error");
      setMessage(optionMessage || "لطفاً گزینه‌های محصول را انتخاب کنید.");
      return;
    }

    if (
      normalizedAvailableStock !== null &&
      quantity > normalizedAvailableStock
    ) {
      setMessageTone("error");
      setMessage(getStockLimitMessage(normalizedAvailableStock));
      return;
    }

    setIsSubmitting(true);

    try {
      await addCartItem(accessToken, productId, quantity, selectedOptions);
      setMessageTone("success");
      setMessage("محصول به سبد خرید اضافه شد.");
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        clearTokens();
        logout();
        router.push("/login");
        setMessageTone("error");
        setMessage("برای ادامه لطفا دوباره وارد شوید.");
        return;
      }

      setMessageTone("error");
      setMessage(
        getCartErrorMessage(
          error,
          "افزودن کالا به سبد خرید انجام نشد. لطفاً دوباره تلاش کنید.",
          normalizedAvailableStock,
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mt-7 space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <QuantitySelector
          disabled={isSubmitting || !isInStock}
          max={normalizedAvailableStock ?? undefined}
          onChange={setQuantity}
          value={quantity}
        />
        <Button
          className="min-h-12 w-full px-6 py-3 text-center leading-6 whitespace-normal sm:w-auto sm:min-w-56 sm:flex-1"
          disabled={
            isSubmitting ||
            !isInStock ||
            (requiresOptions && Boolean(optionMessage))
          }
          onClick={handleAddToCart}
          type="button"
          variant="coral"
        >
          {isSubmitting ? "در حال افزودن..." : "افزودن به سبد خرید"}
        </Button>
      </div>

      {message ? (
        <p
          className={
            messageTone === "success"
              ? "rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 ring-1 ring-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-100 dark:ring-emerald-800/50"
              : "rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700 ring-1 ring-rose-100 dark:bg-rose-950/45 dark:text-rose-100 dark:ring-rose-800/50"
          }
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
