"use client";

import { ArrowLeft, ChevronLeft, ChevronRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  getHomepageSectionSlots,
  getHomepageSections,
  normalizeHomepageSections,
} from "@/lib/api/homepage";
import { getProducts } from "@/lib/api/products";
import { formatToman } from "@/lib/format";
import {
  getProductCategoryName,
  getProductImageUrl,
  getProductPrice,
  getProductShortDescription,
} from "@/lib/product-display";
import { cn } from "@/lib/utils";
import type { HomepageProductSlot, Product } from "@/types/api";

const SLIDER_INTERVAL_MS = 5200;

type HeroSlideItem = {
  product: Product;
  slot?: HomepageProductSlot;
};

export function HeroSection() {
  const [slides, setSlides] = useState<HeroSlideItem[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      try {
        const sections = normalizeHomepageSections(await getHomepageSections());
        const heroSlots = getHomepageSectionSlots(sections, "hero_slider");

        if (isMounted) {
          if (heroSlots.length > 0) {
            setSlides(
              heroSlots.map((slot) => ({
                product: slot.product,
                slot,
              })),
            );
            return;
          }

          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 6,
          });
          setSlides(
            response.slice(0, 6).map((product) => ({
              product,
            })),
          );
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Hero products API error:", error);
        }

        try {
          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 6,
          });

          if (isMounted) {
            setSlides(
              response.slice(0, 6).map((product) => ({
                product,
              })),
            );
          }
        } catch (fallbackError) {
          if (process.env.NODE_ENV !== "production") {
            console.error("Hero fallback products API error:", fallbackError);
          }
        }
      }
    }

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (slides.length <= 1) {
      return;
    }

    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % slides.length);
    }, SLIDER_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [slides.length]);

  const activeSlide = slides[activeIndex];

  function goToPreviousSlide() {
    setActiveIndex((current) =>
      current === 0 ? slides.length - 1 : current - 1,
    );
  }

  function goToNextSlide() {
    setActiveIndex((current) => (current + 1) % slides.length);
  }

  return (
    <section className="relative isolate overflow-hidden px-4 pb-10 pt-5 sm:px-6 sm:pb-12 lg:px-8">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_84%_8%,rgb(var(--color-sunshine)/0.46),transparent_20rem),radial-gradient(circle_at_12%_20%,rgb(var(--color-grape)/0.18),transparent_23rem),radial-gradient(circle_at_42%_90%,rgb(var(--color-coral)/0.16),transparent_25rem)]" />
      <div className="mx-auto max-w-7xl lg:min-h-[calc(100svh-5.5rem)]">
        {activeSlide ? (
          <HeroSlide
            activeIndex={activeIndex}
            onNext={goToNextSlide}
            onPrevious={goToPreviousSlide}
            onSelect={setActiveIndex}
            slide={activeSlide}
            slideCount={slides.length}
          />
        ) : (
          <HeroFallback />
        )}
      </div>
    </section>
  );
}

function HeroSlide({
  slide,
  activeIndex,
  slideCount,
  onNext,
  onPrevious,
  onSelect,
}: {
  slide: HeroSlideItem;
  activeIndex: number;
  slideCount: number;
  onNext: () => void;
  onPrevious: () => void;
  onSelect: (index: number) => void;
}) {
  const { product, slot } = slide;
  const imageUrl = getProductImageUrl(product);
  const title = slot?.title_override || product.name;
  const subtitle = slot?.subtitle_override || getProductShortDescription(product);
  const shortDescription = subtitle ? truncateText(subtitle, 140) : "";

  return (
    <div className="relative flex overflow-hidden rounded-[2rem] border border-white/70 bg-white/72 p-5 shadow-soft backdrop-blur dark:border-white/10 sm:rounded-[2.5rem] sm:p-8 lg:min-h-[calc(100svh-5.5rem)] lg:items-center lg:p-10">
      <div className="pointer-events-none absolute -right-16 top-16 size-48 rounded-full bg-candy/18 blur-3xl" />
      <div className="pointer-events-none absolute -left-20 bottom-10 size-56 rounded-full bg-mint/20 blur-3xl" />
      <div className="grid w-full items-center gap-7 sm:gap-9 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="relative z-10 order-2 lg:order-1">
          <div className="inline-flex items-center gap-2 rounded-full bg-cream/85 px-4 py-2 text-sm font-black text-coral shadow-sm ring-1 ring-white/70 dark:ring-white/10">
            <Sparkles className="size-4" />
            بنر ویژه فروشگاه IpakToys
          </div>

          <div className="animate-hero-slide-in" key={product.slug}>
            <p className="mt-7 text-sm font-black text-grape">
              {getProductCategoryName(product)}
            </p>
            <h1 className="mt-3 max-w-3xl text-[clamp(1.85rem,4.8vw,3.25rem)] font-black leading-[1.32] tracking-tight text-ink">
              {title}
            </h1>
            {shortDescription ? (
              <p className="mt-5 max-w-2xl text-base leading-9 text-slate-700 dark:text-slate-300 sm:text-lg sm:leading-10">
                {shortDescription}
              </p>
            ) : null}
            <p className="mt-6 text-3xl font-black text-coral">
              {formatToman(getProductPrice(product))}
            </p>
          </div>

          <div className="mt-8 flex flex-col gap-3 min-[420px]:flex-row">
            <Button asChild className="h-12 px-7" size="lg" variant="coral">
              <Link href={`/products/${product.slug}`}>
                مشاهده محصول <ArrowLeft className="size-5" />
              </Link>
            </Button>
            <Button asChild className="h-12 px-7" size="lg" variant="outline">
              <Link href="/products">خرید بازی‌ها</Link>
            </Button>
          </div>

          {slideCount > 1 ? (
            <div className="mt-8 flex items-center gap-3">
              <button
                aria-label="اسلاید قبلی"
                className="flex size-11 items-center justify-center rounded-2xl bg-white/80 text-ink shadow-sm ring-1 ring-white/70 transition hover:text-coral dark:bg-white/10 dark:ring-white/10"
                onClick={onPrevious}
                type="button"
              >
                <ChevronRight className="size-5" />
              </button>
              <div className="flex items-center gap-2">
                {Array.from({ length: slideCount }).map((_, index) => (
                  <button
                    aria-label={`نمایش اسلاید ${index + 1}`}
                    className={cn(
                      "h-2.5 rounded-full transition",
                      index === activeIndex
                        ? "w-8 bg-coral"
                        : "w-2.5 bg-ink/20 hover:bg-coral/60",
                    )}
                    key={index}
                    onClick={() => onSelect(index)}
                    type="button"
                  />
                ))}
              </div>
              <button
                aria-label="اسلاید بعدی"
                className="flex size-11 items-center justify-center rounded-2xl bg-white/80 text-ink shadow-sm ring-1 ring-white/70 transition hover:text-coral dark:bg-white/10 dark:ring-white/10"
                onClick={onNext}
                type="button"
              >
                <ChevronLeft className="size-5" />
              </button>
            </div>
          ) : null}
        </div>

        <div className="relative order-1 lg:order-2">
          <div className="absolute inset-0 animate-soft-float rounded-[3rem] bg-gradient-to-br from-sunshine/55 via-coral/20 to-grape/24 blur-2xl" />
          <div className="relative mx-auto flex h-[18rem] max-w-xl items-center justify-center overflow-hidden rounded-[2.3rem] bg-gradient-to-br from-skysoft via-cream to-sunshine/50 p-4 shadow-soft ring-1 ring-white/80 dark:ring-white/10 min-[420px]:h-[21rem] sm:h-[30rem] sm:rounded-[3rem] sm:p-5 lg:h-[34rem]">
            {imageUrl ? (
              <div
                aria-label={product.name}
                className="h-full w-full rounded-[1.9rem] bg-cover bg-center shadow-card sm:rounded-[2.4rem]"
                role="img"
                style={{ backgroundImage: `url("${imageUrl}")` }}
              />
            ) : (
              <div className="size-40 rounded-[2rem] bg-white/70 shadow-card sm:size-48 sm:rounded-[3rem]" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function HeroFallback() {
  return (
    <div className="flex rounded-[2rem] border border-white/70 bg-white/72 p-6 shadow-soft backdrop-blur dark:border-white/10 sm:rounded-[2.5rem] sm:p-8 lg:min-h-[calc(100svh-5.5rem)] lg:items-center">
      <div className="max-w-3xl">
        <p className="text-sm font-black text-coral">IpakToys</p>
        <h1 className="mt-4 text-[clamp(1.85rem,4.8vw,3.25rem)] font-black leading-[1.32] text-ink">
          دنیای بازی‌های فکری، بردگیم و سرگرمی‌های ساختنی
        </h1>
        <p className="mt-5 text-base leading-9 text-ink/65 sm:text-lg">
          محصولات فروشگاه در حال دریافت هستند. برای دیدن همه محصولات وارد صفحه
          محصولات شوید.
        </p>
        <Button asChild className="mt-8 h-12 px-7" size="lg" variant="coral">
          <Link href="/products">مشاهده محصولات</Link>
        </Button>
      </div>
    </div>
  );
}

function truncateText(value: string, maxLength: number) {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength).trim()}...`;
}
