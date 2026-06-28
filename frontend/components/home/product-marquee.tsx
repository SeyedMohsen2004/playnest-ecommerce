"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getProducts } from "@/lib/api/products";
import { formatToman } from "@/lib/format";
import {
  getProductImageUrl,
  getProductPrice,
  type ProductSource,
} from "@/lib/product-display";
import type { Product } from "@/types/api";

export function ProductMarquee() {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      try {
        const response = await getProducts({ ordering: "-created_at" });

        if (isMounted) {
          setProducts(response);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Product marquee API error:", error);
        }
      }
    }

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, []);

  const marqueeProducts = useMemo(() => {
    if (products.length === 0) {
      return [];
    }

    return [...products, ...products];
  }, [products]);

  if (marqueeProducts.length === 0) {
    return null;
  }

  return (
    <section
      className="pb-12 pt-1 sm:pb-14 sm:pt-2"
      aria-label="محصولات فروشگاه"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-[2.5rem] border border-white/70 bg-white/78 p-4 shadow-card backdrop-blur dark:border-white/10 sm:p-6">
          <div className="mb-5 flex items-center justify-between gap-4 px-2">
            <p className="text-base font-black text-ink sm:text-lg">
              محصولات تازه فروشگاه
            </p>
            <Link className="text-sm font-bold text-coral" href="/products">
              مشاهده همه
            </Link>
          </div>
          <div className="group relative overflow-hidden">
            <div className="flex w-max gap-5 will-change-transform animate-marquee-rtl sm:gap-6">
              {marqueeProducts.map((product, index) => (
                <MarqueeProductCard
                  key={`${product.slug}-${index}`}
                  product={product}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function MarqueeProductCard({ product }: { product: ProductSource }) {
  const imageUrl = getProductImageUrl(product);

  return (
    <Link
      className="flex w-[18rem] shrink-0 items-center gap-4 rounded-[1.9rem] bg-cream/70 p-4 text-right shadow-sm ring-1 ring-ink/5 transition hover:-translate-y-1 hover:bg-white hover:shadow-card dark:ring-white/10 dark:hover:bg-white/10 sm:w-[20rem] sm:gap-5 sm:p-5 lg:w-[21rem]"
      href={`/products/${product.slug}`}
    >
      <span className="relative size-28 shrink-0 overflow-hidden rounded-[1.5rem] bg-gradient-to-br from-skysoft to-sunshine/40 sm:size-32">
        {imageUrl ? (
          <span
            aria-label={product.name}
            className="block h-full w-full bg-cover bg-center"
            role="img"
            style={{ backgroundImage: `url("${imageUrl}")` }}
          />
        ) : null}
      </span>
      <span className="min-w-0">
        <span className="line-clamp-2 text-base font-black leading-7 text-ink sm:text-lg sm:leading-8">
          {product.name}
        </span>
        <span className="mt-2 block text-sm font-black text-coral sm:text-base">
          {formatToman(getProductPrice(product))}
        </span>
      </span>
    </Link>
  );
}
