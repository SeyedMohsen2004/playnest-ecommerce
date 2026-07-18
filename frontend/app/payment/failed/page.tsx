import { Suspense } from "react";

import { PaymentFailedClient } from "@/app/payment/failed/payment-failed-client";

export default function PaymentFailedPage() {
  return (
    <Suspense fallback={<ResultLoading />}>
      <PaymentFailedClient />
    </Suspense>
  );
}

function ResultLoading() {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm dark:bg-slate-900/80 dark:text-white/70">
        در حال بررسی وضعیت سفارش...
      </div>
    </section>
  );
}
