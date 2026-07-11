"use client";

import { LogIn, PackageOpen, Trash2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { PriceText } from "@/components/shared/price-text";
import { QuantitySelector } from "@/components/shared/quantity-selector";
import { Button } from "@/components/ui/button";
import {
  getCart,
  removeCartItem,
  updateCartItem,
} from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman } from "@/lib/format";
import {
  getProductCategoryName,
  getProductImageClass,
  getProductImageUrl,
  getProductPrice,
} from "@/lib/product-display";
import { cn } from "@/lib/utils";
import type { Cart, CartItem } from "@/types/api";

const discount = 0;
const shipping = 0;

export default function CartPage() {
  const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [mutatingItemId, setMutatingItemId] = useState<number | null>(null);

  const handleUnauthorized = useCallback(() => {
    clearTokens();
    logout();
    setErrorMessage("نشست شما منقضی شده است. لطفا دوباره وارد شوید.");
  }, [logout]);

  const loadCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      setIsLoading(false);
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage("");

    try {
      setCart(await getCart(accessToken));
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage("خطا در دریافت سبد خرید. لطفا کمی بعد دوباره تلاش کنید.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [handleUnauthorized, isAuthenticated]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    loadCart();
  }, [isAuthLoading, loadCart]);

  async function mutateCartItem(
    itemId: number,
    mutation: (accessToken: string) => Promise<unknown>,
  ) {
    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    setMutatingItemId(itemId);
    setErrorMessage("");

    try {
      await mutation(accessToken);
      await loadCart();
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage("خطا در به‌روزرسانی سبد خرید.");
      }
    } finally {
      setMutatingItemId(null);
    }
  }

  const items = cart?.items || [];
  const subtotal = useMemo(() => getCartSubtotal(cart), [cart]);
  const total = Math.max(0, subtotal - discount + shipping);

  return (
    <>
      <PageHeader
        description="محصولات انتخاب‌شده را بررسی کنید و برای ثبت سفارش ادامه دهید."
        title="سبد خرید"
      />
      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[1fr_24rem] lg:px-8">
        {isAuthLoading || isLoading ? (
          <div className="lg:col-span-2 rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm">
            در حال دریافت سبد خرید...
          </div>
        ) : !isAuthenticated ? (
          <div className="lg:col-span-2">
            <LoginRequiredState />
          </div>
        ) : items.length === 0 ? (
          <div className="lg:col-span-2">
            <EmptyState
              description="هنوز محصولی به سبد خرید اضافه نکرده‌اید."
              icon={PackageOpen}
              title="سبد خرید شما خالی است"
            />
            <div className="mt-5 text-center">
              <Button asChild variant="coral">
                <Link href="/products">مشاهده محصولات</Link>
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {errorMessage ? (
                <p className="rounded-3xl bg-rose-50 px-5 py-4 text-sm font-bold leading-7 text-rose-700">
                  {errorMessage}
                </p>
              ) : null}

              {items.map((item) => (
                <CartItemRow
                  disabled={mutatingItemId === item.id}
                  item={item}
                  key={item.id}
                  onRemove={() =>
                    mutateCartItem(item.id, (accessToken) =>
                      removeCartItem(accessToken, item.id),
                    )
                  }
                  onUpdateQuantity={(quantity) =>
                    mutateCartItem(item.id, (accessToken) =>
                      updateCartItem(accessToken, item.id, quantity),
                    )
                  }
                />
              ))}
            </div>

            <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black text-ink">خلاصه سفارش</h2>
              <div className="mt-6 space-y-4 text-sm">
                <SummaryRow label="جمع محصولات" value={subtotal} />
                <SummaryRow label="تخفیف" value={-discount} />
                <SummaryRow label="هزینه ارسال" value={shipping} />
              </div>
              <p className="mt-3 text-xs leading-6 text-ink/45">
                تخفیف و هزینه ارسال در مرحله تسویه حساب نهایی می‌شود.
              </p>
              <div className="mt-6 border-t border-ink/10 pt-5">
                <SummaryRow large label="مبلغ قابل پرداخت" value={total} />
              </div>
              <Button asChild className="mt-6 w-full" variant="coral">
                <Link href="/checkout">ادامه خرید و تسویه حساب</Link>
              </Button>
              <Button asChild className="mt-3 w-full" variant="outline">
                <Link href="/products">ادامه خرید</Link>
              </Button>
            </aside>
          </>
        )}
      </section>
    </>
  );
}

function LoginRequiredState() {
  return (
    <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral">
        <LogIn className="size-8" aria-hidden="true" />
      </span>
      <h2 className="mt-5 text-2xl font-black text-ink">
        برای مشاهده سبد خرید وارد شوید
      </h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-ink/60">
        سبد خرید شما به حساب کاربری متصل است. برای ادامه خرید ابتدا وارد حساب
        خود شوید.
      </p>
      <Button asChild className="mt-6" variant="coral">
        <Link href="/login">ورود به حساب کاربری</Link>
      </Button>
    </div>
  );
}

function CartItemRow({
  item,
  disabled,
  onUpdateQuantity,
  onRemove,
}: {
  item: CartItem;
  disabled: boolean;
  onUpdateQuantity: (quantity: number) => void;
  onRemove: () => void;
}) {
  const imageUrl = getProductImageUrl(item.product);
  const imageClass = getProductImageClass(item.product);

  return (
    <article className="grid gap-4 rounded-[2rem] bg-white p-4 shadow-sm sm:grid-cols-[8rem_1fr_auto] sm:items-center">
      <div
        className={cn(
          "h-32 overflow-hidden rounded-3xl bg-gradient-to-br",
          imageClass,
        )}
      >
        {imageUrl ? (
          <div
            aria-label={item.product.name}
            className="h-full w-full bg-cover bg-center"
            role="img"
            style={{ backgroundImage: `url("${imageUrl}")` }}
          />
        ) : null}
      </div>
      <div>
        <p className="text-xs font-bold text-coral">
          {getProductCategoryName(item.product)}
        </p>
        <Link href={`/products/${item.product.slug}`}>
          <h2 className="mt-2 text-xl font-black text-ink transition hover:text-coral">
            {item.product.name}
          </h2>
        </Link>
        <PriceText amount={getProductPrice(item.product)} className="mt-3" />
        <p className="mt-2 text-xs font-bold text-ink/45">
          جمع این ردیف: {formatToman(getCartItemTotal(item))}
        </p>
      </div>
      <div className="flex items-center justify-between gap-3 sm:flex-col sm:items-end">
        <QuantitySelector
          disabled={disabled}
          onChange={onUpdateQuantity}
          value={item.quantity}
        />
        <button
          className="flex items-center gap-2 text-sm font-bold text-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled}
          onClick={onRemove}
          type="button"
        >
          <Trash2 className="size-4" />
          حذف
        </button>
      </div>
    </article>
  );
}

function SummaryRow({
  label,
  value,
  large = false,
}: {
  label: string;
  value: number;
  large?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className={large ? "font-black text-ink" : "text-ink/60"}>
        {label}
      </span>
      <span className={large ? "text-xl font-black text-ink" : "font-bold text-ink"}>
        {formatToman(value)}
      </span>
    </div>
  );
}

function getCartItemTotal(item: CartItem) {
  return (
    item.line_total ||
    item.subtotal ||
    getProductPrice(item.product) * item.quantity
  );
}

function getCartSubtotal(cart: Cart | null) {
  if (!cart) {
    return 0;
  }

  return (
    cart.subtotal ||
    cart.subtotal_amount ||
    cart.total_price ||
    cart.items.reduce((sum, item) => sum + getCartItemTotal(item), 0)
  );
}
