"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ProductCard } from "@/components/product/product-card";
import { Button } from "@/components/ui/button";
import {
  getHomepageSectionProducts,
  getHomepageSections,
  normalizeHomepageSections,
} from "@/lib/api/homepage";
import { getProducts } from "@/lib/api/products";
import { toPersianDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Product } from "@/types/api";

const AUTOPLAY_INTERVAL_MS = 4000;
const TRANSITION_RESET_MS = 760;
const MAX_VISIBLE_DOTS = 7;

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

function getVisibleDotIndexes(totalItems: number, activeIndex: number) {
  if (totalItems <= MAX_VISIBLE_DOTS) {
    return Array.from({ length: totalItems }, (_, index) => index);
  }

  const sideCount = Math.floor(MAX_VISIBLE_DOTS / 2);
  let start = activeIndex - sideCount;
  let end = activeIndex + sideCount;

  if (start < 0) {
    start = 0;
    end = MAX_VISIBLE_DOTS - 1;
  }

  if (end >= totalItems) {
    end = totalItems - 1;
    start = totalItems - MAX_VISIBLE_DOTS;
  }

  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

export function LatestProductsCarousel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [visibleCount, setVisibleCount] = useState(4);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isTransitionEnabled, setIsTransitionEnabled] = useState(true);

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
        const sections = normalizeHomepageSections(await getHomepageSections());
        const homepageProducts = getHomepageSectionProducts(
          sections,
          "latest_carousel",
        );

        if (isMounted) {
          if (homepageProducts.length > 0) {
            setProducts(homepageProducts);
          } else {
            const response = await getProducts({
              ordering: "-created_at",
              page: 1,
              page_size: 12,
            });
            setProducts(response);
          }
          setActiveIndex(0);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Latest products carousel API error:", error);
        }

        try {
          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 12,
          });

          if (isMounted) {
            setProducts(response);
            setActiveIndex(0);
          }
        } catch (fallbackError) {
          if (process.env.NODE_ENV !== "production") {
            console.error(
              "Latest products carousel fallback API error:",
              fallbackError,
            );
          }

          if (isMounted) {
            setProducts([]);
            setHasError(true);
          }
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

  const canSlide = products.length > visibleCount;
  const itemBasis = `${100 / visibleCount}%`;
  const logicalActiveIndex =
    products.length > 0 ? activeIndex % products.length : 0;
  const visibleDotIndexes = useMemo(
    () => getVisibleDotIndexes(products.length, logicalActiveIndex),
    [logicalActiveIndex, products.length],
  );
  const positionLabel =
    products.length > 0
      ? `${toPersianDigits(logicalActiveIndex + 1)} / ${toPersianDigits(products.length)}`
      : "";
  const trackProducts = useMemo(() => {
    if (products.length === 0) {
      return [];
    }

    return products.concat(products.slice(0, visibleCount));
  }, [products, visibleCount]);

  useEffect(() => {
    if (products.length === 0) {
      setActiveIndex(0);
      return;
    }

    setActiveIndex((current) => Math.min(current, products.length - 1));
  }, [products.length, visibleCount]);

  useEffect(() => {
    if (activeIndex < products.length || products.length === 0) {
      return;
    }

    const resetTimer = window.setTimeout(() => {
      setIsTransitionEnabled(false);
      setActiveIndex(0);

      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => setIsTransitionEnabled(true));
      });
    }, TRANSITION_RESET_MS);

    return () => window.clearTimeout(resetTimer);
  }, [activeIndex, products.length]);

  useEffect(() => {
    if (isPaused || !canSlide) {
      return;
    }

    const timer = window.setInterval(() => {
      setIsTransitionEnabled(true);
      setActiveIndex((current) => current + 1);
    }, AUTOPLAY_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [canSlide, isPaused]);

  function goToPreviousItem() {
    if (!canSlide) {
      return;
    }

    setIsTransitionEnabled(true);
    setActiveIndex((current) =>
      current <= 0 ? Math.max(products.length - 1, 0) : current - 1,
    );
  }

  function goToNextItem() {
    if (!canSlide) {
      return;
    }

    setIsTransitionEnabled(true);
    setActiveIndex((current) => current + 1);
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
            <p className="text-[0.8125rem] font-black uppercase tracking-wide text-coral">
              تازه‌های فروشگاه
            </p>
            <h2 className="mt-2 text-[1.375rem] font-black tracking-tight text-ink sm:text-[1.75rem]">
              تازه‌ترین محصولات فروشگاه
            </h2>
            <p className="mt-3 max-w-2xl text-[0.8125rem] leading-7 text-ink/60">
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

          {!isLoading && !hasError && trackProducts.length > 0 ? (
            <>
              <div className="overflow-hidden">
                <div
                  className={cn(
                    "flex ease-out",
                    isTransitionEnabled
                      ? "transition-transform duration-700"
                      : "transition-none",
                  )}
                  style={{
                    transform: `translateX(${activeIndex * (100 / visibleCount)}%)`,
                  }}
                >
                  {trackProducts.map((product, index) => (
                    <div
                      className="shrink-0 px-2.5"
                      key={`${product.slug}-${index}`}
                      style={{ flexBasis: itemBasis }}
                    >
                      <ProductCard product={product} />
                    </div>
                  ))}
                </div>
              </div>

              {canSlide ? (
                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  <button
                    aria-label="اسلاید قبلی محصولات"
                    className="flex size-11 items-center justify-center rounded-2xl bg-white/85 text-ink shadow-sm ring-1 ring-white/70 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine"
                    onClick={goToPreviousItem}
                    type="button"
                  >
                    <ChevronRight className="size-5" />
                  </button>
                  <div className="flex max-w-full items-center justify-center gap-2 rounded-full bg-white/60 px-3 py-2 shadow-sm ring-1 ring-white/70 dark:bg-white/10 dark:ring-white/10">
                    {visibleDotIndexes.map((index) => (
                      <button
                        aria-label={`نمایش محصول ${index + 1}`}
                        className={cn(
                          "h-2.5 rounded-full transition",
                          index === logicalActiveIndex
                            ? "w-8 bg-coral"
                            : "w-2.5 bg-ink/20 hover:bg-coral/60 dark:bg-white/25",
                        )}
                        key={index}
                        onClick={() => {
                          setIsTransitionEnabled(true);
                          setActiveIndex(index);
                        }}
                        type="button"
                      />
                    ))}
                    <span className="mr-1 whitespace-nowrap text-xs font-black text-ink/55 dark:text-white/60">
                      {positionLabel}
                    </span>
                  </div>
                  <button
                    aria-label="اسلاید بعدی محصولات"
                    className="flex size-11 items-center justify-center rounded-2xl bg-white/85 text-ink shadow-sm ring-1 ring-white/70 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine"
                    onClick={goToNextItem}
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
