"use client";

import { XCircle } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { getOrder } from "@/lib/api/orders";
import { requestPayment } from "@/lib/api/payments";
import { getAccessToken } from "@/lib/auth/token-storage";
import type { Order } from "@/types/api";

const reasonMessages: Record<string, string> = {
  missing_authority: "اطلاعات بازگشت از درگاه کامل نبود.",
  invalid_callback_status: "وضعیت بازگشتی درگاه معتبر نبود.",
  payment_not_found: "تراکنش موردنظر پیدا نشد.",
  cancelled_or_failed: "پرداخت در درگاه لغو شد یا تکمیل نشد.",
  verification_failed: "تأیید پرداخت توسط درگاه انجام نشد.",
  verification_unavailable: "ارتباط با درگاه برای تأیید نهایی برقرار نشد.",
  finalization_failed: "ثبت نهایی نتیجه پرداخت نیازمند بررسی است.",
  order_cancelled: "این سفارش پیش از تأیید پرداخت لغو شده بود.",
};

export function PaymentFailedClient() {
  const searchParams = useSearchParams();
  const orderId = Number(searchParams.get("order_id"));
  const reason = searchParams.get("reason") || "";
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (isAuthLoading) return;

    async function loadOrderState() {
      if (!isAuthenticated || !Number.isFinite(orderId) || orderId <= 0) {
        setIsLoading(false);
        return;
      }
      const accessToken = getAccessToken();
      if (!accessToken) {
        setIsLoading(false);
        return;
      }
      try {
        setOrder(await getOrder(accessToken, orderId));
      } catch {
        setErrorMessage("امکان دریافت وضعیت سفارش وجود ندارد.");
      } finally {
        setIsLoading(false);
      }
    }

    loadOrderState();
  }, [isAuthenticated, isAuthLoading, orderId]);

  async function handleRetry() {
    if (!order) return;
    const accessToken = getAccessToken();
    if (!accessToken) return;

    setIsRetrying(true);
    setErrorMessage("");
    try {
      const payment = await requestPayment(accessToken, order.id);
      if (!payment.payment_url) throw new Error("Payment URL was not returned.");
      window.location.assign(payment.payment_url);
    } catch {
      setErrorMessage("آماده‌سازی پرداخت مجدد انجام نشد. لطفاً دوباره تلاش کنید.");
      setIsRetrying(false);
    }
  }

  if (isAuthLoading || isLoading) {
    return <ResultCard>در حال بررسی وضعیت سفارش...</ResultCard>;
  }

  const authoritativePaid = order?.payment_status === "paid";

  return (
    <ResultCard>
      <XCircle className="mx-auto size-16 text-rose-600" aria-hidden="true" />
      <h1 className="mt-5 text-3xl font-black text-ink dark:text-white">
        پرداخت ناموفق بود
      </h1>
      <p className="mt-3 text-sm leading-7 text-ink/60 dark:text-white/60">
        سفارش شما ثبت شده اما پرداخت انجام نشده است.
      </p>
      <p className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold leading-7 text-rose-700 dark:bg-rose-950/40 dark:text-rose-100">
        {authoritativePaid
          ? "پرداخت این سفارش در سرور تأیید شده است؛ جزئیات سفارش را مشاهده کنید."
          : reasonMessages[reason] || "پرداخت تکمیل نشد. می‌توانید از جزئیات سفارش دوباره تلاش کنید."}
      </p>
      {errorMessage ? (
        <p className="mt-4 text-sm font-bold text-rose-700 dark:text-rose-200">
          {errorMessage}
        </p>
      ) : null}
      <div className="mt-7 grid gap-3 sm:grid-cols-2">
        {order?.can_retry_payment ? (
          <Button
            disabled={isRetrying}
            onClick={handleRetry}
            type="button"
            variant="coral"
          >
            {isRetrying ? "در حال انتقال..." : "تلاش مجدد برای پرداخت"}
          </Button>
        ) : null}
        {Number.isFinite(orderId) && orderId > 0 ? (
          <Button asChild variant="outline">
            <Link href={`/account/orders/${orderId}`}>جزئیات سفارش</Link>
          </Button>
        ) : null}
        <Button asChild variant="outline">
          <Link href="/cart">بازگشت به سبد خرید</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/account/orders">سفارش‌های من</Link>
        </Button>
      </div>
    </ResultCard>
  );
}

function ResultCard({ children }: { children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="rounded-[2rem] bg-white p-8 text-center shadow-sm dark:bg-slate-900/80 sm:p-10">
        {children}
      </div>
    </section>
  );
}
