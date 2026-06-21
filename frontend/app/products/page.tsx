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
      <ProductsPageClient />
    </>
  );
}
