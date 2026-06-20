"use client";

import { Heart, ShoppingCart, Star } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { PriceText } from "@/components/shared/price-text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { addCartItem } from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import {
  getProductBadge,
  getProductCategoryName,
  getProductImageClass,
  getProductImageUrl,
  getProductIsInStock,
  getProductOldPrice,
  getProductPrice,
  getProductRating,
  isApiProduct,
  type ProductSource,
} from "@/lib/product-display";
import { toPersianDigits } from "@/lib/format";
import { cn } from "@/lib/utils";

export function ProductCard({ product }: { product: ProductSource }) {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const imageUrl = getProductImageUrl(product);
  const imageClass = getProductImageClass(product);
  const isInStock = getProductIsInStock(product);
  const productId = isApiProduct(product) ? product.id : null;
  const [isAdding, setIsAdding] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<"success" | "error">(
    "success",
  );

  async function handleAddToCart() {
    setMessage("");

    if (!isAuthenticated) {
      setMessageTone("error");
      setMessage("برای افزودن به سبد خرید ابتدا وارد شوید.");
      router.push("/login");
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      clearTokens();
      logout();
      router.push("/login");
      return;
    }

    if (typeof productId !== "number" || !Number.isFinite(productId)) {
      setMessageTone("error");
      setMessage("خطا در افزودن به سبد خرید.");
      return;
    }

    setIsAdding(true);

    try {
      await addCartItem(accessToken, productId, 1);
      setMessageTone("success");
      setMessage("به سبد خرید اضافه شد.");
    } catch (error) {
      if (process.env.NODE_ENV !== "production") {
        console.error("Product card add to cart error:", error);
      }

      if (error instanceof APIError && error.status === 401) {
        clearTokens();
        logout();
        router.push("/login");
        return;
      }

      setMessageTone("error");
      setMessage("خطا در افزودن به سبد خرید.");
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <article className="group overflow-hidden rounded-3xl border border-ink/5 bg-white text-right shadow-sm transition hover:-translate-y-1 hover:shadow-soft">
      <Link href={`/products/${product.slug}`} className="block">
        <div
          className={cn(
            "relative flex h-52 items-center justify-center overflow-hidden bg-gradient-to-br",
            imageClass,
          )}
        >
          {imageUrl ? (
            <div
              aria-label={product.name}
              className="absolute inset-0 bg-cover bg-center transition duration-500 group-hover:scale-105"
              role="img"
              style={{ backgroundImage: `url("${imageUrl}")` }}
            />
          ) : (
            <div className="size-24 rotate-6 rounded-[2rem] bg-white/70 shadow-soft transition group-hover:rotate-12" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-ink/20 via-transparent to-transparent" />
          <Badge className="absolute right-4 top-4 bg-white/90 text-coral">
            {getProductBadge(product)}
          </Badge>
          <button
            type="button"
            className="absolute left-4 top-4 flex size-10 items-center justify-center rounded-full bg-white/90 text-ink shadow-sm transition hover:text-coral"
            aria-label={`افزودن ${product.name} به علاقه‌مندی‌ها`}
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
          >
            <Heart className="size-5" />
          </button>
        </div>
      </Link>

      <div className="p-5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-bold uppercase tracking-wide text-ink/45">
            {getProductCategoryName(product)}
          </p>
          <span
            className={cn(
              "rounded-full px-2.5 py-1 text-xs font-black",
              isInStock
                ? "bg-emerald-100 text-emerald-700"
                : "bg-rose-100 text-rose-700",
            )}
          >
            {isInStock ? "موجود" : "ناموجود"}
          </span>
        </div>
        <Link href={`/products/${product.slug}`}>
          <h3 className="mt-2 min-h-14 text-lg font-black leading-7 text-ink transition hover:text-coral">
            {product.name}
          </h3>
        </Link>
        <div className="mt-3 flex items-center gap-1 text-sm font-bold text-amber-500">
          <Star className="size-4 fill-current" />
          {toPersianDigits(getProductRating(product).toFixed(1))}
        </div>
        <PriceText
          amount={getProductPrice(product)}
          className="mt-4"
          oldAmount={getProductOldPrice(product)}
        />
        <Button
          className="mt-5 w-full"
          disabled={isAdding || !isInStock}
          onClick={handleAddToCart}
          type="button"
          variant="outline"
        >
          <ShoppingCart className="size-4" />
          {isAdding
            ? "در حال افزودن..."
            : isInStock
              ? "افزودن به سبد خرید"
              : "ناموجود"}
        </Button>
        {message ? (
          <p
            className={
              messageTone === "success"
                ? "mt-3 rounded-2xl bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700"
                : "mt-3 rounded-2xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700"
            }
          >
            {message}
          </p>
        ) : null}
      </div>
    </article>
  );
}
