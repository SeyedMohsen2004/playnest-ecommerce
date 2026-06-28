"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/product/product-card";
import { Button } from "@/components/ui/button";
import { getProducts } from "@/lib/api/products";
import { cn } from "@/lib/utils";
import type { Product } from "@/types/api";

const AUTOPLAY_INTERVAL_MS = 6200;

function getVisibleCount() {
  if (typeof window === "undefined") {
    return 4;
  }

  if (window.innerWidth < 640) {
    return 1;
  }

  if (window.innerWidth < 1024) {
    return 2;
  }

  if (window.innerWidth < 1280) {
    return 3;
  }

  return 4;
}

export function LatestProductsCarousel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [visibleCount, setVisibleCount] = useState(4);
  const [pageIndex, setPageIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    function updateVisibleCount() {
      setVisibleCount(getVisibleCount());
    }

    updateVisibleCount();
    window.addEventListener("resize", updateVisibleCount);

    return () => window.removeEventListener("resize", updateVisibleCount);
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      setIsLoading(true);
      setHasError(false);

      try {
        const response = await getProducts({ ordering: "-created_at" });

        if (isMounted) {
          setProducts(response);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Latest products carousel API error:", error);
        }

        if (isMounted) {
          setProducts([]);
          setHasError(true);
        }
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
  }, []);

  const pageCount = Math.max(1, Math.ceil(products.length / visibleCount));

  useEffect(() => {
    setPageIndex((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  useEffect(() => {
    if (isPaused || pageCount <= 1) {
      return;
    }

    const timer = window.setInterval(() => {
      setPageIndex((current) => (current + 1) % pageCount);
    }, AUTOPLAY_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [isPaused, pageCount]);

  const visibleProducts = useMemo(() => {
    const startIndex = pageIndex * visibleCount;
    const currentPageProducts = products.slice(
      startIndex,
      startIndex + visibleCount,
    );

    if (currentPageProducts.length === visibleCount || products.length === 0) {
      return currentPageProducts;
    }

    return currentPageProducts.concat(
      products.slice(0, visibleCount - currentPageProducts.length),
    );
  }, [pageIndex, products, visibleCount]);

  function goToPreviousPage() {
    setPageIndex((current) => (current === 0 ? pageCount - 1 : current - 1));
  }

  function goToNextPage() {
    setPageIndex((current) => (current + 1) % pageCount);
  }

  return (
    <section
      className="relative overflow-hidden px-4 py-12 sm:px-6 lg:px-8"
      aria-label="تازه‌ترین محصولات فروشگاه"
    >
      <div className="pointer-events-none absolute left-10 top-8 size-40 rounded-full bg-coral/10 blur-3xl" />
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-black uppercase tracking-wide text-coral">
              تازه‌های فروشگاه
            </p>
            <h2 className="mt-2 text-3xl font-black tracking-tight text-ink sm:text-4xl">
              تازه‌ترین محصولات فروشگاه
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-ink/60">
              جدیدترین بازی‌های فکری، بردگیم‌ها، پازل‌ها و محصولات ساختنی
              IpakToys را در یک اسلایدر مرحله‌ای ببینید.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/products">مشاهده همه محصولات</Link>
          </Button>
        </div>

        <div
          className="rounded-[2.4rem] border border-white/70 bg-white/70 p-4 shadow-soft backdrop-blur dark:border-white/10 sm:p-5"
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
        >
          {isLoading ? (
            <div className="rounded-[2rem] bg-white/85 p-10 text-center text-sm font-black text-ink/60 dark:bg-white/10">
              در حال دریافت تازه‌ترین محصولات...
            </div>
          ) : null}

          {!isLoading && hasError ? (
            <div className="rounded-[2rem] border border-rose-100 bg-rose-50 p-6 text-center text-sm font-bold leading-7 text-rose-700 dark:border-rose-800/50 dark:bg-rose-950/40 dark:text-rose-100">
              خطا در دریافت محصولات. لطفاً کمی بعد دوباره تلاش کنید.
            </div>
          ) : null}

          {!isLoading && !hasError && visibleProducts.length > 0 ? (
            <>
              <div
                className={cn(
                  "grid gap-5 transition duration-500",
                  visibleCount === 1
                    ? "grid-cols-1"
                    : visibleCount === 2
                      ? "grid-cols-1 sm:grid-cols-2"
                      : visibleCount === 3
                        ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
                        : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
                )}
                key={`${pageIndex}-${visibleCount}`}
              >
                {visibleProducts.map((product) => (
                  <ProductCard key={`${pageIndex}-${product.slug}`} product={product} />
                ))}
              </div>

              {pageCount > 1 ? (
                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  <button
                    aria-label="اسلاید قبلی محصولات"
                    className="flex size-11 items-center justify-center rounded-2xl bg-white/85 text-ink shadow-sm ring-1 ring-white/70 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine"
                    onClick={goToPreviousPage}
                    type="button"
                  >
                    <ChevronRight className="size-5" />
                  </button>
                  <div className="flex items-center gap-2">
                    {Array.from({ length: pageCount }).map((_, index) => (
                      <button
                        aria-label={`نمایش گروه ${index + 1}`}
                        className={cn(
                          "h-2.5 rounded-full transition",
                          index === pageIndex
                            ? "w-8 bg-coral"
                            : "w-2.5 bg-ink/20 hover:bg-coral/60 dark:bg-white/25",
                        )}
                        key={index}
                        onClick={() => setPageIndex(index)}
                        type="button"
                      />
                    ))}
                  </div>
                  <button
                    aria-label="اسلاید بعدی محصولات"
                    className="flex size-11 items-center justify-center rounded-2xl bg-white/85 text-ink shadow-sm ring-1 ring-white/70 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine"
                    onClick={goToNextPage}
                    type="button"
                  >
                    <ChevronLeft className="size-5" />
                  </button>
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </section>
  );
}
