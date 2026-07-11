"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProductCard } from "@/components/product/product-card";
import { Button } from "@/components/ui/button";
import {
  getHomepageSectionProducts,
  getHomepageSections,
  normalizeHomepageSections,
} from "@/lib/api/homepage";
import { getProducts } from "@/lib/api/products";
import type { Product } from "@/types/api";

export function FeaturedProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      setIsLoading(true);
      setHasError(false);

      try {
        const sections = normalizeHomepageSections(await getHomepageSections());
        const homepageProducts = getHomepageSectionProducts(
          sections,
          "featured_products",
        );

        if (!isMounted) {
          return;
        }

        if (homepageProducts.length > 0) {
          setProducts(homepageProducts);
          return;
        }

        const response = await getProducts({
          ordering: "-created_at",
          page: 1,
          page_size: 4,
        });
        setProducts(response.slice(0, 4));
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Homepage products API error:", error);
        }

        try {
          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 4,
          });

          if (isMounted) {
            setProducts(response.slice(0, 4));
          }
        } catch (fallbackError) {
          if (process.env.NODE_ENV !== "production") {
            console.error("Homepage products fallback API error:", fallbackError);
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

  return (
    <section className="relative overflow-hidden bg-white/55 py-16" id="offers">
      <div className="pointer-events-none absolute left-10 top-10 size-32 rounded-full bg-coral/10 blur-3xl" />
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-coral">
              محصولات منتخب
            </p>
            <h2 className="mt-3 text-2xl font-black tracking-tight text-ink sm:text-3xl">
              انتخاب‌های واقعی IpakToys برای بازی، فکر و دورهمی.
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-7 text-ink/60">
            این بخش مستقیما از محصولات ثبت‌شده فروشگاه خوانده می‌شود تا فقط
            کالاهای واقعی واردشده نمایش داده شوند.
          </p>
        </div>

        {isLoading ? (
          <div className="mt-8 rounded-[2rem] bg-white/85 p-10 text-center text-sm font-black text-ink/60 shadow-card backdrop-blur">
            در حال دریافت محصولات فروشگاه...
          </div>
        ) : null}

        {!isLoading && hasError ? (
          <div className="mt-8 rounded-[2rem] border border-rose-100 bg-rose-50 p-6 text-center text-sm font-bold leading-7 text-rose-700">
            خطا در دریافت محصولات صفحه اصلی. لطفا اتصال بک‌اند را بررسی کنید.
          </div>
        ) : null}

        {!isLoading && !hasError && products.length === 0 ? (
          <div className="mt-8 rounded-[2rem] bg-white/85 p-8 text-center shadow-card backdrop-blur">
            <p className="text-sm font-bold leading-7 text-ink/60">
              هنوز محصولی برای نمایش در صفحه اصلی ثبت نشده است.
            </p>
            <Button asChild className="mt-4">
              <Link href="/products">مشاهده همه محصولات</Link>
            </Button>
          </div>
        ) : null}

        {!isLoading && !hasError && products.length > 0 ? (
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((product) => (
              <ProductCard key={product.slug} product={product} />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
