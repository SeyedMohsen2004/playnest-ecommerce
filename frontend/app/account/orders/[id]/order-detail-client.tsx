"use client";

import { LogIn, PackageOpen } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { APIError } from "@/lib/api/client";
import { getOrder } from "@/lib/api/orders";
import { requestPayment } from "@/lib/api/payments";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman, toPersianDigits } from "@/lib/format";
import { normalizeImageUrl } from "@/lib/product-display";
import type { Order, OrderItem } from "@/types/api";

export function OrderDetailClient({ orderId }: { orderId: string }) {
  const numericOrderId = Number(orderId);
  const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleUnauthorized = useCallback(() => {
    clearTokens();
    logout();
    setErrorMessage("نشست شما منقضی شده است. لطفا دوباره وارد شوید.");
  }, [logout]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    async function loadOrder() {
      if (!isAuthenticated) {
        setOrder(null);
        setIsLoading(false);
        return;
      }

      const accessToken = getAccessToken();
      if (!accessToken) {
        handleUnauthorized();
        setIsLoading(false);
        return;
      }

      if (!Number.isFinite(numericOrderId)) {
        setErrorMessage("سفارش پیدا نشد.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setErrorMessage("");

      try {
        setOrder(await getOrder(accessToken, numericOrderId));
      } catch (error) {
        if (error instanceof APIError && error.status === 401) {
          handleUnauthorized();
        } else {
          setErrorMessage("سفارش پیدا نشد.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadOrder();
  }, [handleUnauthorized, isAuthenticated, isAuthLoading, numericOrderId]);

  async function handleRetryPayment() {
    const accessToken = getAccessToken();
    if (!accessToken || !order) {
      handleUnauthorized();
      return;
    }

    setIsRetrying(true);
    setErrorMessage("");

    try {
      const response = await requestPayment(accessToken, order.id);
      if (response.payment_url) {
        window.location.href = response.payment_url;
        return;
      }
      window.location.href = `/payment/${order.id}`;
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage(getPaymentRetryError(error));
      }
    } finally {
      setIsRetrying(false);
    }
  }

  return (
    <>
      <PageHeader
        description="جزئیات سفارش، محصولات، وضعیت پرداخت و اطلاعات ارسال را اینجا ببینید."
        title="جزئیات سفارش"
      />
      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        {isAuthLoading || isLoading ? (
          <StateCard>در حال دریافت اطلاعات سفارش...</StateCard>
        ) : !isAuthenticated ? (
          <LoginRequiredState />
        ) : errorMessage && !order ? (
          <StateCard>{errorMessage}</StateCard>
        ) : order ? (
          <div className="grid gap-6 lg:grid-cols-[1fr_24rem]">
            <div className="space-y-5">
              {errorMessage ? (
                <p className="rounded-3xl bg-rose-50 px-5 py-4 text-sm font-bold leading-7 text-rose-700 dark:bg-rose-950/45 dark:text-rose-100">
                  {errorMessage}
                </p>
              ) : null}

              <article className="rounded-[2rem] bg-white p-6 shadow-sm dark:bg-slate-900/80">
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
                  <Detail label="شماره سفارش" value={`#${toPersianDigits(order.id)}`} />
                  <Detail label="تاریخ ثبت سفارش" value={formatDate(order.created_at)} />
                  <div>
                    <p className="text-xs font-bold text-ink/45 dark:text-white/45">
                      وضعیت سفارش
                    </p>
                    <div className="mt-2">
                      <StatusBadge status={order.status} />
                    </div>
                  </div>
                  <Detail
                    label="وضعیت پرداخت"
                    value={order.payment_status_label || "ثبت نشده"}
                  />
                </div>
              </article>

              <article className="rounded-[2rem] bg-white p-6 shadow-sm dark:bg-slate-900/80">
                <h2 className="text-xl font-black text-ink dark:text-white">
                  محصولات سفارش
                </h2>
                <div className="mt-5 space-y-4">
                  {order.items?.map((item) => (
                    <OrderItemRow item={item} key={item.id} />
                  ))}
                </div>
              </article>

              <article className="rounded-[2rem] bg-white p-6 shadow-sm dark:bg-slate-900/80">
                <h2 className="text-xl font-black text-ink dark:text-white">
                  اطلاعات مشتری و ارسال
                </h2>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <Detail label="نام گیرنده" value={order.recipient_name} />
                  <Detail label="شماره موبایل" value={order.recipient_phone} />
                  <Detail label="کد پستی" value={order.postal_code} />
                  <Detail label="آدرس ارسال" value={order.shipping_address} />
                </div>
              </article>
            </div>

            <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm dark:bg-slate-900/80 lg:sticky lg:top-28">
              <h2 className="text-2xl font-black text-ink dark:text-white">
                خلاصه سفارش
              </h2>
              <div className="mt-6 space-y-4 text-sm">
                <Summary label="جمع محصولات" value={formatToman(order.subtotal_amount)} />
                <Summary label="تخفیف" value={formatToman(order.discount_amount)} />
                <Summary label="هزینه ارسال" value={formatToman(order.shipping_cost)} />
                <Summary
                  strong
                  label="مبلغ کل"
                  value={formatToman(order.total_amount)}
                />
              </div>
              <div className="mt-6 grid gap-3">
                {order.can_retry_payment ? (
                  <Button
                    disabled={isRetrying}
                    onClick={handleRetryPayment}
                    type="button"
                    variant="coral"
                  >
                    {isRetrying ? "در حال آماده‌سازی..." : "پرداخت مجدد"}
                  </Button>
                ) : null}
                <Button asChild variant="outline">
                  <Link href="/account/orders">بازگشت به سفارش‌های من</Link>
                </Button>
              </div>
            </aside>
          </div>
        ) : (
          <StateCard>سفارش پیدا نشد.</StateCard>
        )}
      </section>
    </>
  );
}

function OrderItemRow({ item }: { item: OrderItem }) {
  const imageUrl = normalizeImageUrl(item.product_image?.image);

  return (
    <div className="grid gap-4 rounded-3xl border border-ink/10 p-4 dark:border-white/10 sm:grid-cols-[6rem_1fr]">
      <div className="h-24 overflow-hidden rounded-2xl bg-gradient-to-br from-sky-100 via-rose-50 to-amber-100">
        {imageUrl ? (
          <div
            aria-label={item.product_name}
            className="h-full w-full bg-cover bg-center"
            role="img"
            style={{ backgroundImage: `url("${imageUrl}")` }}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-coral">
            <PackageOpen className="size-8" aria-hidden="true" />
          </div>
        )}
      </div>
      <div>
        <Link
          className="text-lg font-black text-ink transition hover:text-coral dark:text-white"
          href={item.product_slug ? `/products/${item.product_slug}` : "/products"}
        >
          {item.product_name}
        </Link>
        <div className="mt-3 grid gap-2 text-sm text-ink/60 dark:text-white/60 sm:grid-cols-3">
          <span>تعداد: {toPersianDigits(item.quantity)}</span>
          <span>قیمت واحد: {formatToman(item.unit_price || item.product_price)}</span>
          <span>قیمت کل: {formatToman(item.total_price || item.line_total)}</span>
        </div>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-bold text-ink/45 dark:text-white/45">{label}</p>
      <p className="mt-2 font-black leading-7 text-ink dark:text-white">{value}</p>
    </div>
  );
}

function Summary({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-ink/5 pb-3 last:border-b-0 dark:border-white/10">
      <span className="text-ink/60 dark:text-white/60">{label}</span>
      <span
        className={
          strong
            ? "text-lg font-black text-ink dark:text-white"
            : "font-bold text-ink dark:text-white"
        }
      >
        {value}
      </span>
    </div>
  );
}

function StateCard({ children }: { children: string }) {
  return (
    <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm dark:bg-slate-900/80 dark:text-white/70">
      {children}
    </div>
  );
}

function LoginRequiredState() {
  return (
    <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm dark:border-white/10 dark:bg-slate-900/80">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral dark:bg-slate-800">
        <LogIn className="size-8" aria-hidden="true" />
      </span>
      <h2 className="mt-5 text-2xl font-black text-ink dark:text-white">
        برای مشاهده سفارش وارد شوید
      </h2>
      <Button asChild className="mt-6" variant="coral">
        <Link href="/login">ورود به حساب کاربری</Link>
      </Button>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

function getPaymentRetryError(error: unknown) {
  if (error instanceof APIError) {
    const data = error.data as
      | { detail?: unknown; items?: Array<{ product_name?: string }> }
      | undefined;

    const detail = Array.isArray(data?.detail) ? data.detail[0] : data?.detail;

    if (typeof detail === "string") {
      const itemNames = data?.items
        ?.map((item) => item.product_name)
        .filter(Boolean)
        .join("، ");

      return itemNames ? `${detail} (${itemNames})` : detail;
    }
  }

  return "امکان آماده‌سازی پرداخت وجود ندارد. لطفاً دوباره تلاش کنید.";
}
