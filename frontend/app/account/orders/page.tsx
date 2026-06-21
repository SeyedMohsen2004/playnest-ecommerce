import Link from "next/link";

import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { orders } from "@/lib/mock-data";

export default function AccountOrdersPage() {
  return (
    <>
      <PageHeader
        description="وضعیت سفارش‌ها، مبلغ پرداختی و روند ارسال را از این بخش دنبال کنید."
        title="سفارش‌های من"
      />
      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="space-y-4">
          {orders.map((order) => (
            <article
              id={`order-${order.id}`}
              className="grid gap-4 rounded-[2rem] bg-white p-5 shadow-sm md:grid-cols-[1fr_auto] md:items-center"
              key={order.id}
            >
              <div className="grid gap-4 sm:grid-cols-4 sm:items-center">
                <div>
                  <p className="text-xs font-bold text-ink/45">شماره سفارش</p>
                  <h2 className="mt-1 text-xl font-black text-ink">
                    #{new Intl.NumberFormat("fa-IR").format(order.id)}
                  </h2>
                </div>
                <div>
                  <p className="text-xs font-bold text-ink/45">وضعیت</p>
                  <div className="mt-2">
                    <StatusBadge status={order.status} />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-ink/45">تاریخ</p>
                  <p className="mt-2 font-bold text-ink">{order.date}</p>
                </div>
                <div>
                  <p className="text-xs font-bold text-ink/45">مبلغ سفارش</p>
                  <p className="mt-2 font-black text-ink">
                    {new Intl.NumberFormat("fa-IR").format(order.total)} تومان
                  </p>
                </div>
              </div>
              <Button asChild variant="outline">
                <Link href={`/account/orders#order-${order.id}`}>
                  مشاهده جزئیات
                </Link>
              </Button>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
