import { ProductCard } from "@/components/product/product-card";
import { featuredProducts } from "@/lib/mock-data";

export function FeaturedProducts() {
  return (
    <section className="bg-white/70 py-16" id="products">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
          <p className="text-sm font-bold uppercase tracking-wide text-coral">
              محصولات ویژه
          </p>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-ink sm:text-4xl">
              انتخاب‌های محبوب برای بچه‌های شاد.
          </h2>
        </div>
        <p className="max-w-xl text-sm leading-6 text-ink/60">
            این محصولات فعلا با داده‌های نمونه نمایش داده می‌شوند و اتصال به API
            در مرحله بعدی توسعه فرانت‌اند انجام می‌شود.
        </p>
        </div>

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featuredProducts.map((product) => (
            <ProductCard key={product.name} product={product} />
          ))}
        </div>
      </div>
    </section>
  );
}
