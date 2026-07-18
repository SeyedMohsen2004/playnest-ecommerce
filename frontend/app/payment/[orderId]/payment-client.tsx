"use client";

import { CreditCard, LogIn } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { APIError } from "@/lib/api/client";
import { getOrder } from "@/lib/api/orders";
import { requestPayment } from "@/lib/api/payments";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman, toPersianDigits } from "@/lib/format";
import type { Order } from "@/types/api";

export function PaymentClient({ orderId }: { orderId: string }) {
  const numericOrderId = Number(orderId);
  const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRequesting, setIsRequesting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleUnauthorized = useCallback(() => {
    clearTokens();
    logout();
    setErrorMessage("نشست شما منقضی شده است. لطفاً دوباره وارد شوید.");
  }, [logout]);

  useEffect(() => {
    if (isAuthLoading) return;

    async function loadOrder() {
      if (!isAuthenticated || !Number.isFinite(numericOrderId)) {
        setIsLoading(false);
        return;
      }
      const accessToken = getAccessToken();
      if (!accessToken) {
        handleUnauthorized();
        setIsLoading(false);
        return;
      }
      try {
        setOrder(await getOrder(accessToken, numericOrderId));
      } catch (error) {
        if (error instanceof APIError && error.status === 401) {
          handleUnauthorized();
        } else {
          setErrorMessage("سفارش پیدا نشد یا امکان پرداخت آن وجود ندارد.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadOrder();
  }, [handleUnauthorized, isAuthenticated, isAuthLoading, numericOrderId]);

  async function handlePayment() {
    if (!order) return;
    const accessToken = getAccessToken();
    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    setIsRequesting(true);
    setErrorMessage("");
    try {
      const payment = await requestPayment(accessToken, order.id);
      if (!payment.payment_url) {
        throw new Error("Payment URL was not returned.");
      }
      window.location.assign(payment.payment_url);
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage("آماده‌سازی درگاه پرداخت انجام نشد. لطفاً دوباره تلاش کنید.");
      }
      setIsRequesting(false);
    }
  }

  if (isAuthLoading || isLoading) {
    return <StateCard>در حال آماده‌سازی پرداخت...</StateCard>;
  }

  if (!isAuthenticated) {
    return (
      <StateCard>
        <LogIn className="mx-auto size-9 text-coral" aria-hidden="true" />
        <p className="mt-4">برای پرداخت سفارش وارد حساب کاربری خود شوید.</p>
        <Button asChild className="mt-5" variant="coral">
          <Link href="/login">ورود به حساب کاربری</Link>
        </Button>
      </StateCard>
    );
  }

  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="rounded-[2rem] bg-white p-6 shadow-sm dark:bg-slate-900/80 sm:p-8">
        <span className="flex size-16 items-center justify-center rounded-3xl bg-coral/10 text-coral">
          <CreditCard className="size-8" aria-hidden="true" />
        </span>
        <p className="mt-6 text-sm font-bold text-coral">پرداخت امن زرین‌پال</p>
        <h1 className="mt-2 text-3xl font-black text-ink dark:text-white">
          سفارش شماره {toPersianDigits(orderId)}
        </h1>
        {order ? (
          <div className="mt-6 rounded-3xl bg-cream p-5 dark:bg-slate-950/60">
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-ink/60 dark:text-white/60">مبلغ قابل پرداخت</span>
              <strong className="text-lg text-ink dark:text-white">
                {formatToman(order.total_amount)}
              </strong>
            </div>
          </div>
        ) : null}
        <p className="mt-5 text-sm leading-7 text-ink/60 dark:text-white/60">
          با انتخاب دکمه پرداخت به درگاه رسمی زرین‌پال منتقل می‌شوید. نتیجه
          نهایی پرداخت فقط پس از تأیید سرور نمایش داده می‌شود.
        </p>
        {errorMessage ? (
          <p className="mt-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700 dark:bg-rose-950/40 dark:text-rose-100">
            {errorMessage}
          </p>
        ) : null}
        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          {order?.can_retry_payment ? (
            <Button
              disabled={isRequesting}
              onClick={handlePayment}
              type="button"
              variant="coral"
            >
              {isRequesting ? "در حال انتقال به درگاه..." : "پرداخت با زرین‌پال"}
            </Button>
          ) : null}
          <Button asChild variant="outline">
            <Link href={`/account/orders/${orderId}`}>مشاهده جزئیات سفارش</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

function StateCard({ children }: { children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm dark:bg-slate-900/80 dark:text-white/70">
        {children}
      </div>
    </section>
  );
}
