"use client";

import { CheckCircle2, LogIn } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { getCart } from "@/lib/api/cart";
import { getOrder } from "@/lib/api/orders";
import { getAccessToken } from "@/lib/auth/token-storage";
import { toPersianDigits } from "@/lib/format";
import type { Order } from "@/types/api";

export function PaymentSuccessClient() {
  const searchParams = useSearchParams();
  const orderId = Number(searchParams.get("order_id"));
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (isAuthLoading) return;

    async function loadAuthoritativeResult() {
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
        const loadedOrder = await getOrder(accessToken, orderId);
        setOrder(loadedOrder);
        await getCart(accessToken);
      } catch {
        setErrorMessage("امکان دریافت وضعیت نهایی سفارش وجود ندارد.");
      } finally {
        setIsLoading(false);
      }
    }

    loadAuthoritativeResult();
  }, [isAuthenticated, isAuthLoading, orderId]);

  if (isAuthLoading || isLoading) {
    return <ResultCard>در حال بررسی نتیجه پرداخت...</ResultCard>;
  }

  if (!isAuthenticated) {
    return (
      <ResultCard>
        <LogIn className="mx-auto size-10 text-coral" aria-hidden="true" />
        <p className="mt-4">برای مشاهده نتیجه معتبر پرداخت وارد شوید.</p>
        <Button asChild className="mt-5" variant="coral">
          <Link href="/login">ورود به حساب کاربری</Link>
        </Button>
      </ResultCard>
    );
  }

  const isAuthoritativelyPaid =
    order?.payment_status === "paid" &&
    ["paid", "processing", "shipped", "delivered"].includes(order.status);

  if (!isAuthoritativelyPaid) {
    return (
      <ResultCard>
        <p className="text-lg font-black text-ink dark:text-white">
          وضعیت پرداخت هنوز تأیید نشده است.
        </p>
        <p className="mt-3 text-sm leading-7 text-ink/60 dark:text-white/60">
          {errorMessage || "لطفاً جزئیات سفارش را بررسی کنید یا کمی بعد دوباره تلاش کنید."}
        </p>
        {Number.isFinite(orderId) ? (
          <Button asChild className="mt-5" variant="outline">
            <Link href={`/account/orders/${orderId}`}>جزئیات سفارش</Link>
          </Button>
        ) : null}
      </ResultCard>
    );
  }

  return (
    <ResultCard>
      <CheckCircle2 className="mx-auto size-16 text-emerald-600" aria-hidden="true" />
      <h1 className="mt-5 text-3xl font-black text-ink dark:text-white">
        پرداخت با موفقیت انجام شد
      </h1>
      <p className="mt-3 text-sm leading-7 text-ink/60 dark:text-white/60">
        سفارش شماره {toPersianDigits(order.id)} با موفقیت ثبت و تأیید شد.
      </p>
      {order.requires_manual_review ? (
        <p className="mt-5 rounded-2xl bg-amber-50 px-4 py-3 text-sm font-bold leading-7 text-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
          {order.manual_review_message ||
            "پرداخت با موفقیت انجام شد و سفارش برای بررسی موجودی در حال پیگیری است."}
        </p>
      ) : null}
      {order.payment_ref_id ? (
        <p className="mt-5 text-sm text-ink/60 dark:text-white/60">
          شماره پیگیری: <strong dir="ltr">{order.payment_ref_id}</strong>
        </p>
      ) : null}
      <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
        <Button asChild variant="coral">
          <Link href={`/account/orders/${order.id}`}>مشاهده سفارش</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/">بازگشت به خانه</Link>
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
