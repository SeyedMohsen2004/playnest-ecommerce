import { Suspense } from "react";
import type { Metadata } from "next";

import { ProductsPageClient } from "@/components/product/products-page-client";
import { PageHeader } from "@/components/shared/page-header";
import { absoluteUrl, SITE_NAME } from "@/lib/seo";

export const metadata: Metadata = {
  title: {
    absolute: "محصولات | ایپک تویز",
  },
  description:
    "مشاهده و خرید بازی فکری، بردگیم، پازل، لگو و اسباب‌بازی از فروشگاه ایپک تویز در تبریز.",
  alternates: {
    canonical: absoluteUrl("/products"),
  },
  openGraph: {
    title: `خرید اسباب‌بازی، بازی فکری و بردگیم | ${SITE_NAME}`,
    description:
      "محصولات ایپک تویز شامل بازی فکری، بردگیم، پازل، لگو و سرگرمی‌های خانوادگی.",
    url: absoluteUrl("/products"),
    siteName: SITE_NAME,
    locale: "fa_IR",
    type: "website",
  },
};

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
