"use client";

import { useEffect, useMemo, useState } from "react";

import {
  FilterSidebar,
  type FilterOption,
  type ProductFilters,
} from "@/components/product/filter-sidebar";
import { ProductGrid } from "@/components/product/product-grid";
import {
  getBrands,
  getCategories,
  getProducts,
  type ProductQueryParams,
} from "@/lib/api/products";
import { brands as mockBrands, categories as mockCategories } from "@/lib/mock-data";
import { toPersianDigits } from "@/lib/format";
import type { ProductSource } from "@/lib/product-display";

const initialFilters: ProductFilters = {
  search: "",
  category: "",
  brand: "",
  age_group: "",
  ordering: "",
};

export function ProductsPageClient() {
  const [filters, setFilters] = useState<ProductFilters>(initialFilters);
  const [products, setProducts] = useState<ProductSource[]>([]);
  const [categories, setCategories] = useState<FilterOption[]>([]);
  const [brands, setBrands] = useState<FilterOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadFilters() {
      try {
        const categoryResponse = await getCategories();

        if (!isMounted) {
          return;
        }

        setCategories(
          categoryResponse.map((category) => ({
            label: category.name,
            value: String(category.id),
          })),
        );
      } catch (error) {
        console.error("Categories API error:", error);

        if (!isMounted) {
          return;
        }

        setCategories(
          mockCategories.map((category) => ({
            label: category.title,
            value: category.slug,
          })),
        );
      }

      try {
        const brandResponse = await getBrands();

        if (!isMounted) {
          return;
        }

        setBrands(
          brandResponse.map((brand) => ({
            label: brand.name,
            value: String(brand.id),
          })),
        );
      } catch (error) {
        console.error("Brands API error:", error);

        if (!isMounted) {
          return;
        }

        setBrands(
          mockBrands.map((brand) => ({
            label: brand.name,
            value: brand.slug,
          })),
        );
      }
    }

    loadFilters();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      setIsLoading(true);

      try {
        const params: ProductQueryParams = {
          search: filters.search || undefined,
          category: filters.category || undefined,
          brand: filters.brand || undefined,
          age_group: filters.age_group || undefined,
          ordering: filters.ordering || undefined,
        };
        const response = await getProducts(params);

        if (!isMounted) {
          return;
        }

        setProducts(response);
        setHasError(false);
      } catch (error) {
        console.error("Products API error:", error);

        if (!isMounted) {
          return;
        }

        setProducts([]);
        setHasError(true);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, [filters]);

  const productCount = useMemo(
    () => toPersianDigits(products.length),
    [products.length],
  );

  return (
    <section
      className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[18rem_1fr] lg:px-8"
      id="filters"
    >
      <FilterSidebar
        brands={brands}
        categories={categories}
        filters={filters}
        onFiltersChange={setFilters}
      />
      <div>
        <div className="mb-5 flex flex-col justify-between gap-3 rounded-3xl bg-white p-4 shadow-sm sm:flex-row sm:items-center">
          <p className="text-sm font-bold text-ink/65">
            {isLoading
              ? "در حال دریافت محصولات..."
              : `نمایش ${productCount} محصول`}
          </p>
          <p className="text-sm text-ink/50">
            محصولات، دسته‌بندی‌ها و برندها به‌صورت به‌روز از فروشگاه دریافت می‌شوند.
          </p>
        </div>

        {hasError ? (
          <div className="mb-5 rounded-3xl border border-rose-100 bg-rose-50 px-5 py-4 text-sm font-bold leading-7 text-rose-700">
            خطا در دریافت محصولات
          </div>
        ) : null}

        {isLoading ? (
          <div className="rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm">
            در حال دریافت محصولات...
          </div>
        ) : (
          <ProductGrid products={products} />
        )}
      </div>
    </section>
  );
}
