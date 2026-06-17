import { FilterSidebar } from "@/components/product/filter-sidebar";
import { ProductGrid } from "@/components/product/product-grid";
import { PageHeader } from "@/components/shared/page-header";
import { products } from "@/lib/mock-data";

export default function ProductsPage() {
  return (
    <>
      <PageHeader
        description="مجموعه‌ای از اسباب‌بازی‌های آموزشی، فکری، ساختنی و سرگرم‌کننده برای سنین مختلف."
        eyebrow="فروشگاه PlayNest"
        title="همه اسباب‌بازی‌ها"
      />
      <section
        className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[18rem_1fr] lg:px-8"
        id="filters"
      >
        <FilterSidebar />
        <div>
          <div className="mb-5 flex flex-col justify-between gap-3 rounded-3xl bg-white p-4 shadow-sm sm:flex-row sm:items-center">
            <p className="text-sm font-bold text-ink/65">
              نمایش {new Intl.NumberFormat("fa-IR").format(products.length)} محصول
            </p>
            <p className="text-sm text-ink/50">
              فیلترها فعلا نمایشی هستند و در مرحله اتصال API فعال می‌شوند.
            </p>
          </div>
          <ProductGrid products={products} />
        </div>
      </section>
    </>
  );
}
