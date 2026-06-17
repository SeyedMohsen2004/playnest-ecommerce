import { PackageSearch } from "lucide-react";

import { ProductCard } from "@/components/product/product-card";
import { EmptyState } from "@/components/shared/empty-state";
import type { ProductSource } from "@/lib/product-display";

export function ProductGrid({ products }: { products: ProductSource[] }) {
  if (products.length === 0) {
    return (
      <EmptyState
        actionLabel="پاک کردن فیلترها"
        description="با تغییر دسته‌بندی یا جستجو می‌توانید محصولات بیشتری را ببینید."
        icon={PackageSearch}
        title="محصولی پیدا نشد"
      />
    );
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {products.map((product) => (
        <ProductCard key={product.slug} product={product} />
      ))}
    </div>
  );
}
