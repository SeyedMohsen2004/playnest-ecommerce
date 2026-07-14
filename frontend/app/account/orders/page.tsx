"use client";

import { LogIn, PackageOpen } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { APIError } from "@/lib/api/client";
import { cancelOrder, getOrders } from "@/lib/api/orders";
import { requestPayment } from "@/lib/api/payments";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman, toPersianDigits } from "@/lib/format";
import type { Order } from "@/types/api";

export default function AccountOrdersPage() {
  const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [retryingOrderId, setRetryingOrderId] = useState<number | null>(null);
  const [cancellingOrderId, setCancellingOrderId] = useState<number | null>(null);

  const handleUnauthorized = useCallback(() => {
    clearTokens();
    logout();
    setErrorMessage("نشست شما منقضی شده است. لطفا دوباره وارد شوید.");
  }, [logout]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    async function loadOrders() {
      if (!isAuthenticated) {
        setOrders([]);
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
      setSuccessMessage("");

      try {
        setOrders(await getOrders(accessToken));
      } catch (error) {
        if (error instanceof APIError && error.status === 401) {
          handleUnauthorized();
        } else {
          setErrorMessage("خطا در دریافت سفارش‌ها. لطفاً دوباره تلاش کنید.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadOrders();
  }, [handleUnauthorized, isAuthenticated, isAuthLoading]);

  async function handleRetryPayment(orderId: number) {
    const accessToken = getAccessToken();
    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    setRetryingOrderId(orderId);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await requestPayment(accessToken, orderId);
      if (response.payment_url) {
        window.location.href = response.payment_url;
        return;
      }
      window.location.href = `/payment/${orderId}`;
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage(getPaymentRetryError(error));
      }
    } finally {
      setRetryingOrderId(null);
    }
  }

  async function handleCancelOrder(orderId: number) {
    if (!window.confirm("آیا از لغو این سفارش مطمئن هستید؟")) {
      return;
    }

    const accessToken = getAccessToken();
    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    setCancellingOrderId(orderId);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const updatedOrder = await cancelOrder(accessToken, orderId);
      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          order.id === orderId ? updatedOrder : order,
        ),
      );
      setSuccessMessage("سفارش با موفقیت لغو شد.");
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage(
          getOrderActionError(error, "امکان لغو این سفارش وجود ندارد."),
        );
      }
    } finally {
      setCancellingOrderId(null);
    }
  }

  return (
    <>
      <PageHeader
        description="وضعیت سفارش‌ها، مبلغ پرداختی و روند ارسال را از این بخش دنبال کنید."
        title="سفارش‌های من"
      />
      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        {isAuthLoading || isLoading ? (
          <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm dark:bg-slate-900/80 dark:text-white/70">
            در حال دریافت سفارش‌ها...
          </div>
        ) : !isAuthenticated ? (
          <LoginRequiredState />
        ) : (
          <div className="space-y-4">
            {successMessage ? (
              <p className="rounded-3xl bg-emerald-50 px-5 py-4 text-sm font-bold leading-7 text-emerald-700 dark:bg-emerald-950/45 dark:text-emerald-100">
                {successMessage}
              </p>
            ) : null}
            {errorMessage ? (
              <p className="rounded-3xl bg-rose-50 px-5 py-4 text-sm font-bold leading-7 text-rose-700 dark:bg-rose-950/45 dark:text-rose-100">
                {errorMessage}
              </p>
            ) : null}
            {orders.length === 0 ? (
              <EmptyState
                description="هنوز سفارشی برای شما ثبت نشده است."
                icon={PackageOpen}
                title="سفارشی پیدا نشد"
              />
            ) : (
              orders.map((order) => (
                <OrderCard
                  cancellingOrderId={cancellingOrderId}
                  key={order.id}
                  onCancelOrder={handleCancelOrder}
                  onRetryPayment={handleRetryPayment}
                  order={order}
                  retryingOrderId={retryingOrderId}
                />
              ))
            )}
          </div>
        )}
      </section>
    </>
  );
}

function OrderCard({
  order,
  retryingOrderId,
  cancellingOrderId,
  onRetryPayment,
  onCancelOrder,
}: {
  order: Order;
  retryingOrderId: number | null;
  cancellingOrderId: number | null;
  onRetryPayment: (orderId: number) => void;
  onCancelOrder: (orderId: number) => void;
}) {
  return (
    <article
      id={`order-${order.id}`}
      className="grid gap-4 rounded-[2rem] bg-white p-5 shadow-sm dark:bg-slate-900/80 md:grid-cols-[1fr_auto] md:items-center"
    >
      <div className="grid gap-4 sm:grid-cols-4 sm:items-center">
        <div>
          <p className="text-xs font-bold text-ink/45 dark:text-white/45">
            شماره سفارش
          </p>
          <h2 className="mt-1 text-xl font-black text-ink dark:text-white">
            #{toPersianDigits(order.id)}
          </h2>
        </div>
        <div>
          <p className="text-xs font-bold text-ink/45 dark:text-white/45">وضعیت</p>
          <div className="mt-2">
            <StatusBadge status={order.status} />
          </div>
        </div>
        <div>
          <p className="text-xs font-bold text-ink/45 dark:text-white/45">تاریخ</p>
          <p className="mt-2 font-bold text-ink dark:text-white">
            {formatDate(order.created_at)}
          </p>
        </div>
        <div>
          <p className="text-xs font-bold text-ink/45 dark:text-white/45">
            مبلغ سفارش
          </p>
          <p className="mt-2 font-black text-ink dark:text-white">
            {formatToman(order.total_amount)}
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row md:flex-col">
        {order.can_retry_payment ? (
          <Button
            disabled={retryingOrderId === order.id || cancellingOrderId === order.id}
            onClick={() => onRetryPayment(order.id)}
            type="button"
            variant="coral"
          >
            {retryingOrderId === order.id ? "در حال آماده‌سازی..." : "پرداخت مجدد"}
          </Button>
        ) : null}
        {order.can_cancel ? (
          <Button
            className="border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 hover:text-rose-800 dark:border-rose-400/25 dark:bg-rose-950/35 dark:text-rose-100 dark:hover:bg-rose-900/55 dark:hover:text-white"
            disabled={retryingOrderId === order.id || cancellingOrderId === order.id}
            onClick={() => onCancelOrder(order.id)}
            type="button"
            variant="outline"
          >
            {cancellingOrderId === order.id ? "در حال لغو..." : "لغو سفارش"}
          </Button>
        ) : null}
        <Button asChild variant="outline">
          <Link href={`/account/orders/${order.id}`}>جزئیات سفارش</Link>
        </Button>
      </div>
    </article>
  );
}

function getPaymentRetryError(error: unknown) {
  return getOrderActionError(
    error,
    "امکان آماده‌سازی پرداخت وجود ندارد. لطفاً دوباره تلاش کنید.",
  );
}

function getOrderActionError(error: unknown, fallbackMessage: string) {
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

  return fallbackMessage;
}

function LoginRequiredState() {
  return (
    <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm dark:border-white/10 dark:bg-slate-900/80">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral dark:bg-slate-800">
        <LogIn className="size-8" aria-hidden="true" />
      </span>
      <h2 className="mt-5 text-2xl font-black text-ink dark:text-white">
        برای مشاهده سفارش‌ها وارد شوید
      </h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-ink/60 dark:text-white/60">
        سفارش‌های شما به حساب کاربری متصل است. برای پیگیری خریدها ابتدا وارد
        حساب خود شوید.
      </p>
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
