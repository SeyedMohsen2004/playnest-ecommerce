"use client";

import { Eye, ShoppingCart, Star } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { PriceText } from "@/components/shared/price-text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { addCartItem } from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { getCartErrorMessage } from "@/lib/api/errors";
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
  getProductReviewCount,
  getProductStock,
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
  const availableStock = getProductStock(product);
  const rating = getProductRating(product);
  const reviewCount = getProductReviewCount(product);
  const [isAdding, setIsAdding] = useState(false);
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
      clearTokens();
      logout();
      router.push("/login");
      return;
    }

    if (typeof productId !== "number" || !Number.isFinite(productId)) {
      setMessageTone("error");
      setMessage("این محصول فعلا از طریق داده نمونه نمایش داده می‌شود.");
      return;
    }

    setIsAdding(true);

    try {
      await addCartItem(accessToken, productId, 1);
      setMessageTone("success");
      setMessage("محصول به سبد خرید اضافه شد.");
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
      setMessage(
        getCartErrorMessage(
          error,
          "افزودن کالا به سبد خرید انجام نشد. لطفاً دوباره تلاش کنید.",
          availableStock,
        ),
      );
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <article className="group overflow-hidden rounded-[2rem] border border-white/75 bg-white/86 text-right shadow-card backdrop-blur transition duration-300 hover:-translate-y-2 hover:shadow-soft">
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
          <Badge className="absolute right-4 top-4 bg-white/92 text-coral shadow-sm">
            {getProductBadge(product)}
          </Badge>
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
        <div className="mt-3 flex items-center gap-1 text-sm font-bold text-ink/50">
          {reviewCount > 0 && rating !== null ? (
            <>
              <Star className="size-4 fill-current text-amber-500" />
              <span className="text-amber-500">
                {toPersianDigits(rating.toFixed(1))}
              </span>
              <span>{toPersianDigits(reviewCount)} نظر</span>
            </>
          ) : (
            <span>بدون نظر</span>
          )}
        </div>
        <PriceText
          amount={getProductPrice(product)}
          className="mt-4"
          oldAmount={getProductOldPrice(product)}
        />
        <div className="mt-5 grid grid-cols-2 gap-2">
          <Button
            asChild
            className="h-11 min-w-0 px-3 text-xs leading-5 sm:px-4 sm:text-sm"
            variant="outline"
          >
            <Link href={`/products/${product.slug}`}>
              <Eye className="size-4" />
              <span className="hidden sm:inline">مشاهده جزئیات</span>
              <span className="sm:hidden">جزئیات</span>
            </Link>
          </Button>
          <Button
            className="h-11 min-w-0 px-3 text-xs leading-5 sm:px-4 sm:text-sm"
            disabled={isAdding || !isInStock}
            onClick={handleAddToCart}
            type="button"
            variant="coral"
          >
            <ShoppingCart className="size-4" />
            {isAdding
              ? "در حال افزودن..."
              : isInStock
                ? "سبد خرید"
                : "ناموجود"}
          </Button>
        </div>
        {message ? (
          <p
            className={
              messageTone === "success"
                ? "mt-3 rounded-2xl bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700 ring-1 ring-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-100 dark:ring-emerald-800/50"
                : "mt-3 rounded-2xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700 ring-1 ring-rose-100 dark:bg-rose-950/45 dark:text-rose-100 dark:ring-rose-800/50"
            }
          >
            {message}
          </p>
        ) : null}
      </div>
    </article>
  );
}
