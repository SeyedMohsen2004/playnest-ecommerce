import { ProductsPageClient } from "@/components/product/products-page-client";
import { PageHeader } from "@/components/shared/page-header";

export default function ProductsPage() {
  return (
    <>
      <PageHeader
        description="مجموعه‌ای از اسباب‌بازی‌های آموزشی، فکری، ساختنی و سرگرم‌کننده برای سنین مختلف."
        eyebrow="فروشگاه PlayNest"
        title="همه اسباب‌بازی‌ها"
      />
      <ProductsPageClient />
    </>
  );
}
