"use client";

import { Heart } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { QuantitySelector } from "@/components/shared/quantity-selector";
import { Button } from "@/components/ui/button";
import { addCartItem } from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";

type ProductCartActionsProps = {
  productId: number | null;
  isInStock: boolean;
};

export function ProductCartActions({
  productId,
  isInStock,
}: ProductCartActionsProps) {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"success" | "error">(
    "success",
  );

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

    setIsSubmitting(true);

    try {
      if (process.env.NODE_ENV !== "production") {
        console.log("Add to cart product id:", productId);
        console.log("Add to cart quantity:", quantity);
        console.log("Add to cart payload keys:", ["product", "quantity"]);
      }

      await addCartItem(accessToken, productId, quantity);
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
      setMessage("خطا در افزودن محصول به سبد خرید.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mt-7 space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <QuantitySelector
          disabled={isSubmitting || !isInStock}
          onChange={setQuantity}
          value={quantity}
        />
        <Button
          className="flex-1"
          disabled={isSubmitting || !isInStock}
          onClick={handleAddToCart}
          type="button"
          variant="coral"
        >
          {isSubmitting ? "در حال افزودن..." : "افزودن به سبد خرید"}
        </Button>
        <Button type="button" variant="outline">
          <Heart className="size-5" />
          علاقه‌مندی
        </Button>
      </div>

      {message ? (
        <p
          className={
            messageTone === "success"
              ? "rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
              : "rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700"
          }
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
