import { PackageOpen, Trash2 } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { PriceText } from "@/components/shared/price-text";
import { QuantitySelector } from "@/components/shared/quantity-selector";
import { Button } from "@/components/ui/button";
import { cartItems } from "@/lib/mock-data";

const subtotal = cartItems.reduce(
  (sum, item) => sum + item.product.price * item.quantity,
  0,
);
const discount = 120000;
const shipping = 50000;
const total = subtotal - discount + shipping;

export default function CartPage() {
  return (
    <>
      <PageHeader
        description="محصولات انتخاب‌شده را بررسی کنید و برای ثبت سفارش ادامه دهید."
        title="سبد خرید"
      />
      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[1fr_24rem] lg:px-8">
        {cartItems.length === 0 ? (
          <div className="lg:col-span-2">
            <EmptyState
              actionLabel="مشاهده محصولات"
              description="هنوز محصولی به سبد خرید اضافه نکرده‌اید."
              icon={PackageOpen}
              title="سبد خرید شما خالی است"
            />
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {cartItems.map((item) => (
                <article
                  className="grid gap-4 rounded-[2rem] bg-white p-4 shadow-sm sm:grid-cols-[8rem_1fr_auto] sm:items-center"
                  key={item.id}
                >
                  <div
                    className={`h-32 rounded-3xl bg-gradient-to-br ${item.product.imageClass}`}
                  />
                  <div>
                    <p className="text-xs font-bold text-coral">
                      {item.product.category}
                    </p>
                    <h2 className="mt-2 text-xl font-black text-ink">
                      {item.product.name}
                    </h2>
                    <PriceText amount={item.product.price} className="mt-3" />
                  </div>
                  <div className="flex items-center justify-between gap-3 sm:flex-col sm:items-end">
                    <QuantitySelector initial={item.quantity} />
                    <button
                      className="flex items-center gap-2 text-sm font-bold text-rose-500"
                      type="button"
                    >
                      <Trash2 className="size-4" />
                      حذف
                    </button>
                  </div>
                </article>
              ))}
            </div>

            <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black text-ink">خلاصه سفارش</h2>
              <div className="mt-6 space-y-4 text-sm">
                <SummaryRow label="جمع محصولات" value={subtotal} />
                <SummaryRow label="تخفیف" value={-discount} />
                <SummaryRow label="هزینه ارسال" value={shipping} />
              </div>
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
        {new Intl.NumberFormat("fa-IR").format(value)} تومان
      </span>
    </div>
  );
}
