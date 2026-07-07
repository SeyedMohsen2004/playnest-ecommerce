"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import {
  FilterSidebar,
  type FilterOption,
  type ProductFilters,
} from "@/components/product/filter-sidebar";
import { ProductGrid } from "@/components/product/product-grid";
import {
  getBrands,
  getCategories,
  getProductsPage,
  type ProductQueryParams,
} from "@/lib/api/products";
import { brands as mockBrands, categories as mockCategories } from "@/lib/mock-data";
import { toPersianDigits } from "@/lib/format";
import type { ProductSource } from "@/lib/product-display";

const PRODUCTS_PAGE_SIZE = 12;

export function ProductsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<ProductSource[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [categories, setCategories] = useState<FilterOption[]>([]);
  const [brands, setBrands] = useState<FilterOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const currentPage = getPageFromSearchParams(searchParams);
  const filters = getFiltersFromSearchParams(searchParams);
  const totalPages = Math.max(1, Math.ceil(totalCount / PRODUCTS_PAGE_SIZE));

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
          page: currentPage,
          page_size: PRODUCTS_PAGE_SIZE,
        };
        const response = await getProductsPage(params);

        if (!isMounted) {
          return;
        }

        setProducts(response.results);
        setTotalCount(response.count);
        setHasError(false);
      } catch (error) {
        console.error("Products API error:", error);

        if (!isMounted) {
          return;
        }

        setProducts([]);
        setTotalCount(0);
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
  }, [
    currentPage,
    filters.age_group,
    filters.brand,
    filters.category,
    filters.ordering,
    filters.search,
  ]);

  const productCount = useMemo(
    () => toPersianDigits(totalCount),
    [totalCount],
  );

  function updateUrl(nextFilters: ProductFilters, nextPage = 1) {
    const params = new URLSearchParams();

    Object.entries(nextFilters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });

    if (nextPage > 1) {
      params.set("page", String(nextPage));
    }

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname, {
      scroll: false,
    });
  }

  function handleFiltersChange(nextFilters: ProductFilters) {
    updateUrl(nextFilters, 1);
  }

  function handlePageChange(page: number) {
    const safePage = Math.min(Math.max(page, 1), totalPages);
    updateUrl(filters, safePage);
  }

  return (
    <section
      className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[18rem_1fr] lg:px-8"
      id="filters"
    >
      <FilterSidebar
        brands={brands}
        categories={categories}
        filters={filters}
        onFiltersChange={handleFiltersChange}
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
          <>
            <ProductGrid products={products} />
            <ProductPaginationControls
              currentPage={currentPage}
              onPageChange={handlePageChange}
              totalPages={totalPages}
            />
          </>
        )}
      </div>
    </section>
  );
}

function getFiltersFromSearchParams(searchParams: URLSearchParams): ProductFilters {
  const ordering = searchParams.get("ordering") || "";
  const ageGroup = searchParams.get("age_group") || "";

  return {
    search: searchParams.get("search") || "",
    category: searchParams.get("category") || "",
    brand: searchParams.get("brand") || "",
    age_group: isValidAgeGroup(ageGroup) ? ageGroup : "",
    ordering: isValidOrdering(ordering) ? ordering : "",
  };
}

function getPageFromSearchParams(searchParams: URLSearchParams) {
  const page = Number(searchParams.get("page") || "1");

  if (!Number.isFinite(page) || page < 1) {
    return 1;
  }

  return Math.floor(page);
}

function isValidOrdering(value: string): value is ProductFilters["ordering"] {
  return ["", "price", "-price", "created_at", "-created_at"].includes(value);
}

function isValidAgeGroup(value: string): value is ProductFilters["age_group"] {
  return ["", "0_2", "3_5", "6_8", "9_12", "12_plus"].includes(value);
}

function ProductPaginationControls({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) {
    return null;
  }

  const pageItems = getPaginationItems(currentPage, totalPages);

  return (
    <nav
      aria-label="صفحه‌بندی محصولات"
      className="mt-8 flex flex-col items-center justify-between gap-4 rounded-[2rem] bg-white/78 p-4 shadow-sm backdrop-blur dark:bg-white/10 sm:flex-row"
    >
      <button
        className="h-11 rounded-2xl bg-cream px-5 text-sm font-black text-ink transition hover:bg-sunshine/30 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-white/10"
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        type="button"
      >
        قبلی
      </button>

      <div className="flex max-w-full flex-wrap items-center justify-center gap-2">
        {pageItems.map((item, index) =>
          item === "ellipsis" ? (
            <span
              className="px-1 text-sm font-black text-ink/45"
              key={`ellipsis-${index}`}
            >
              ...
            </span>
          ) : (
            <button
              aria-current={item === currentPage ? "page" : undefined}
              className={
                item === currentPage
                  ? "flex size-10 items-center justify-center rounded-2xl bg-coral text-sm font-black text-white shadow-sm"
                  : "flex size-10 items-center justify-center rounded-2xl bg-cream text-sm font-black text-ink transition hover:bg-sunshine/30 dark:bg-white/10"
              }
              key={item}
              onClick={() => onPageChange(item)}
              type="button"
            >
              {toPersianDigits(item)}
            </button>
          ),
        )}
      </div>

      <button
        className="h-11 rounded-2xl bg-cream px-5 text-sm font-black text-ink transition hover:bg-sunshine/30 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-white/10"
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        type="button"
      >
        بعدی
      </button>
    </nav>
  );
}

function getPaginationItems(currentPage: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, totalPages, currentPage]);

  if (currentPage > 1) {
    pages.add(currentPage - 1);
  }

  if (currentPage < totalPages) {
    pages.add(currentPage + 1);
  }

  const sortedPages = Array.from(pages).sort((first, second) => first - second);
  const items: Array<number | "ellipsis"> = [];

  sortedPages.forEach((page, index) => {
    const previousPage = sortedPages[index - 1];
    if (previousPage && page - previousPage > 1) {
      items.push("ellipsis");
    }
    items.push(page);
  });

  return items;
}
