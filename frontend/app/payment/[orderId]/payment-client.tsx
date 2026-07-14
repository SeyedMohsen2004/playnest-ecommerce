"use client";

import { CheckCircle2, CreditCard, LogIn, XCircle } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import type { ReactNode } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { APIError } from "@/lib/api/client";
import { requestPayment, verifyPayment } from "@/lib/api/payments";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman, toPersianDigits } from "@/lib/format";
import type {
  Order,
  Payment,
  PaymentRequestResponse,
  PaymentVerifyResponse,
} from "@/types/api";

export function PaymentClient({ orderId }: { orderId: string }) {
  const numericOrderId = Number(orderId);
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [paymentResponse, setPaymentResponse] =
    useState<PaymentRequestResponse | null>(null);
  const [verifyResponse, setVerifyResponse] =
    useState<PaymentVerifyResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isRequesting, setIsRequesting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const authority = getAuthority(paymentResponse);
  const payment = verifyResponse?.payment || paymentResponse?.payment;
  const order = verifyResponse?.order || paymentResponse?.order;
  const amount = getPaymentAmount(paymentResponse, payment, order);
  const isPaid =
    verifyResponse?.payment?.status === "paid" ||
    verifyResponse?.order?.status === "paid";
  const isFailed =
    verifyResponse?.payment?.status === "failed" ||
    verifyResponse?.order?.status === "payment_failed";

  function handleUnauthorized() {
    clearTokens();
    logout();
    setErrorMessage("نشست شما منقضی شده است. لطفا دوباره وارد شوید.");
  }

  async function handleRequestPayment() {
    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    if (!Number.isFinite(numericOrderId)) {
      setErrorMessage("شناسه سفارش معتبر نیست.");
      return;
    }

    setIsRequesting(true);
    setErrorMessage("");

    try {
      const response = await requestPayment(accessToken, numericOrderId);
      setPaymentResponse(response);

      if (response.payment_url) {
        window.open(response.payment_url, "_blank", "noopener,noreferrer");
      }
    } catch (error) {
      if (process.env.NODE_ENV !== "production") {
        console.error("Payment request error:", error);
      }

      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage("پرداخت ناموفق بود یا تایید نشد.");
      }
    } finally {
      setIsRequesting(false);
    }
  }

  async function handleVerifyPayment(status: "OK" | "NOK" = "OK") {
    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    if (!authority) {
      setErrorMessage("کد رهگیری پرداخت برای تایید پیدا نشد.");
      return;
    }

    setIsVerifying(true);
    setErrorMessage("");

    try {
      setVerifyResponse(await verifyPayment(accessToken, authority, status));
    } catch (error) {
      if (process.env.NODE_ENV !== "production") {
        console.error("Payment verify error:", error);
      }

      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setErrorMessage("پرداخت ناموفق بود یا تایید نشد.");
      }
    } finally {
      setIsVerifying(false);
    }
  }

  if (isLoading) {
    return (
      <PaymentShell>
        <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm">
          در حال آماده‌سازی پرداخت...
        </div>
      </PaymentShell>
    );
  }

  if (!isAuthenticated) {
    return (
      <PaymentShell>
        <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm">
          <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral">
            <LogIn className="size-8" />
          </span>
          <h1 className="mt-5 text-2xl font-black text-ink">
            برای پرداخت وارد شوید
          </h1>
          <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-ink/60">
            برای ادامه پرداخت سفارش، ابتدا وارد حساب کاربری خود شوید.
          </p>
          <Button asChild className="mt-6" variant="coral">
            <Link href="/login">ورود به حساب کاربری</Link>
          </Button>
        </div>
      </PaymentShell>
    );
  }

  return (
    <PaymentShell>
      <div className="grid gap-6 lg:grid-cols-[1fr_24rem]">
        <section className="rounded-[2rem] bg-white p-6 shadow-sm sm:p-8">
          <div className="flex size-16 items-center justify-center rounded-3xl bg-coral/10 text-coral">
            <CreditCard className="size-8" />
          </div>
          <p className="mt-6 text-sm font-bold text-coral">پرداخت سفارش</p>
          <h1 className="mt-2 text-3xl font-black text-ink">
            سفارش شماره {toPersianDigits(orderId)}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-ink/60">
            این صفحه فقط شبیه‌ساز پرداخت داخلی برای محیط توسعه است و پرداخت
            واقعی انجام نمی‌دهد. پس از دریافت کد پرداخت، می‌توانید تایید
            آزمایشی را بزنید.
          </p>

          {isPaid ? (
            <div className="mt-6 rounded-3xl bg-emerald-50 p-5 text-emerald-700">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="size-6" />
                <div>
                  <p className="font-black">پرداخت با موفقیت انجام شد.</p>
                  <p className="mt-1 text-sm leading-7">
                    سفارش شما ثبت شد و در انتظار تایید فروشگاه است.
                  </p>
                </div>
              </div>
              <Button asChild className="mt-5" variant="coral">
                <Link href="/account/orders">مشاهده سفارش‌ها</Link>
              </Button>
            </div>
          ) : isFailed ? (
            <div className="mt-6 rounded-3xl bg-rose-50 p-5 text-rose-700">
              <div className="flex items-start gap-3">
                <XCircle className="mt-1 size-6 shrink-0" />
                <div>
                  <p className="font-black">پرداخت ناموفق بود.</p>
                  <p className="mt-1 text-sm leading-7">
                    سفارش شما ثبت شده اما پرداخت انجام نشده است. سبد خرید شما
                    همچنان حفظ شده و می‌توانید دوباره تلاش کنید.
                  </p>
                </div>
              </div>
              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <Button onClick={handleRequestPayment} type="button" variant="coral">
                  تلاش مجدد برای پرداخت
                </Button>
                <Button asChild variant="outline">
                  <Link href="/cart">بازگشت به سبد خرید</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/account/orders">مشاهده سفارش‌ها</Link>
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Button
                disabled={isRequesting}
                onClick={handleRequestPayment}
                type="button"
                variant="coral"
              >
                {isRequesting ? "در حال آماده‌سازی..." : "پرداخت آزمایشی"}
              </Button>
              <Button asChild variant="outline">
                <Link href="/account/orders">بازگشت به سفارش‌ها</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/cart">بازگشت به سبد خرید</Link>
              </Button>
            </div>
          )}

          {paymentResponse?.payment_url && !isPaid ? (
            <div className="mt-6 rounded-3xl bg-skysoft px-5 py-4 text-sm leading-7 text-ink/70">
              لینک درگاه آزمایشی در تب جدید باز شد. اگر باز نشد، از لینک زیر
              استفاده کنید:
              <a
                className="mt-2 block break-all font-bold text-coral"
                href={paymentResponse.payment_url}
                rel="noreferrer"
                target="_blank"
              >
                {paymentResponse.payment_url}
              </a>
            </div>
          ) : null}

          {authority && !isPaid ? (
            <div className="mt-5 rounded-3xl border border-ink/10 bg-cream p-5">
              <p className="text-sm leading-7 text-ink/60">
                کد رهگیری پرداخت آزمایشی آماده است.
              </p>
              <p className="mt-2 break-all text-sm font-black text-ink">
                {authority}
              </p>
              <Button
                className="mt-4"
                disabled={isVerifying}
                onClick={() => handleVerifyPayment("OK")}
                type="button"
                variant="coral"
              >
                {isVerifying
                  ? "در حال تایید پرداخت..."
                  : "تایید پرداخت آزمایشی"}
              </Button>
              <Button
                className="mt-3"
                disabled={isVerifying}
                onClick={() => handleVerifyPayment("NOK")}
                type="button"
                variant="outline"
              >
                ثبت پرداخت ناموفق آزمایشی
              </Button>
            </div>
          ) : null}

          {errorMessage ? (
            <div className="mt-5 rounded-3xl bg-rose-50 p-5 text-rose-700">
              <div className="flex items-center gap-3">
                <XCircle className="size-6" />
                <p className="font-bold">{errorMessage}</p>
              </div>
            </div>
          ) : null}
        </section>

        <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm lg:sticky lg:top-28">
          <h2 className="text-2xl font-black text-ink">خلاصه پرداخت</h2>
          <div className="mt-6 space-y-4 text-sm">
            <SummaryRow label="شماره سفارش" value={toPersianDigits(orderId)} />
            {amount ? (
              <SummaryRow label="مبلغ پرداخت" value={formatToman(amount)} />
            ) : null}
            {payment?.status ? (
              <SummaryRow label="وضعیت پرداخت" value={paymentStatus(payment)} />
            ) : null}
            {order?.status ? (
              <SummaryRow label="وضعیت سفارش" value={orderStatus(order)} />
            ) : null}
          </div>
        </aside>
      </div>
    </PaymentShell>
  );
}

function PaymentShell({ children }: { children: ReactNode }) {
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      {children}
    </section>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-ink/60">{label}</span>
      <span className="font-black text-ink">{value}</span>
    </div>
  );
}

function getAuthority(response: PaymentRequestResponse | null) {
  return response?.authority || response?.payment?.authority || "";
}

function getPaymentAmount(
  response: PaymentRequestResponse | null,
  payment?: Payment,
  order?: Order,
) {
  return response?.amount || payment?.amount || order?.total_amount || 0;
}

function paymentStatus(payment: Payment) {
  const labels: Record<Payment["status"], string> = {
    pending: "در انتظار پرداخت",
    paid: "پرداخت شده",
    failed: "ناموفق",
    cancelled: "لغو شده",
  };

  return labels[payment.status];
}

function orderStatus(order: Order) {
  const labels: Record<Order["status"], string> = {
    pending: "در انتظار پرداخت",
    payment_failed: "پرداخت ناموفق",
    paid: "پرداخت موفق، در انتظار تایید",
    processing: "در حال آماده‌سازی",
    shipped: "ارسال شده",
    delivered: "تحویل داده شده",
    cancelled: "لغو شده",
  };

  return labels[order.status];
}
