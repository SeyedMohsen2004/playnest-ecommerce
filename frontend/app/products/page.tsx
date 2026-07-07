import { Suspense } from "react";

import { ProductsPageClient } from "@/components/product/products-page-client";
import { PageHeader } from "@/components/shared/page-header";

export default function ProductsPage() {
  return (
    <>
      <PageHeader
        description="مجموعه‌ای از بازی‌های فکری، بردگیم‌ها، پازل‌ها، بازی‌های کارتی و محصولات ساختنی برای کودک، نوجوان و خانواده."
        eyebrow="فروشگاه IpakToys"
        title="همه بازی‌ها و محصولات"
      />
      <Suspense
        fallback={
          <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
            <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm">
              در حال بارگذاری محصولات...
            </div>
          </section>
        }
      >
        <ProductsPageClient />
      </Suspense>
    </>
  );
}
