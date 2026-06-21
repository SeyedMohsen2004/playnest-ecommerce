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
import {
  brands as mockBrands,
  categories as mockCategories,
  products as mockProducts,
} from "@/lib/mock-data";
import { toPersianDigits } from "@/lib/format";
import type { ProductSource } from "@/lib/product-display";
import type { Product } from "@/types/api";

const initialFilters: ProductFilters = {
  search: "",
  category: "",
  brand: "",
  age_group: "",
  ordering: "",
};

const ageGroupMockLabels: Record<Product["age_group"], string> = {
  "0_2": "۰ تا ۲ سال",
  "3_5": "۳ تا ۵ سال",
  "6_8": "۶ تا ۸ سال",
  "9_12": "۹ تا ۱۲ سال",
  "12_plus": "۱۲ سال به بالا",
};

function filterMockProducts(filters: ProductFilters) {
  const search = filters.search.trim().toLowerCase();
  const ageGroup = filters.age_group ? ageGroupMockLabels[filters.age_group] : "";

  return mockProducts
    .filter((product) => {
      const matchesSearch =
        !search ||
        product.name.toLowerCase().includes(search) ||
        product.description.toLowerCase().includes(search);
      const matchesCategory =
        !filters.category || product.categorySlug === filters.category;
      const matchesBrand = !filters.brand || product.brandSlug === filters.brand;
      const matchesAgeGroup = !ageGroup || product.ageGroup === ageGroup;

      return matchesSearch && matchesCategory && matchesBrand && matchesAgeGroup;
    })
    .sort((first, second) => {
      if (filters.ordering === "price") {
        return first.price - second.price;
      }

      if (filters.ordering === "-price") {
        return second.price - first.price;
      }

      return 0;
    });
}

export function ProductsPageClient() {
  const [filters, setFilters] = useState<ProductFilters>(initialFilters);
  const [products, setProducts] = useState<ProductSource[]>([]);
  const [categories, setCategories] = useState<FilterOption[]>([]);
  const [brands, setBrands] = useState<FilterOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isFallback, setIsFallback] = useState(false);

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
        setIsFallback(false);
      } catch (error) {
        console.error("Products API error:", error);

        if (!isMounted) {
          return;
        }

        setProducts(filterMockProducts(filters));
        setHasError(true);
        setIsFallback(true);
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
            {isFallback ? "؛ فعلا داده‌های نمونه نمایش داده می‌شوند." : null}
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
