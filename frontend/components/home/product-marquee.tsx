"use client";

import Link from "next/link";
import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";

import {
  getHomepageSectionProducts,
  getHomepageSections,
  normalizeHomepageSections,
} from "@/lib/api/homepage";
import { getProducts } from "@/lib/api/products";
import { formatToman } from "@/lib/format";
import {
  getProductImageUrl,
  getProductPrice,
  type ProductSource,
} from "@/lib/product-display";
import type { HomepageSectionKey, Product } from "@/types/api";

type ProductMarqueeProps = {
  section?: HomepageSectionKey;
  title?: string;
  fallbackToLatestProducts?: boolean;
};

const ORIGINAL_MARQUEE_DURATION_SECONDS = 120;
const DEFAULT_MARQUEE_SPEED_PX_PER_SECOND = 24;

type MarqueeSpeedContextValue = {
  pixelsPerSecond: number;
  setPixelsPerSecond: (speed: number) => void;
};

const MarqueeSpeedContext = createContext<MarqueeSpeedContextValue>({
  pixelsPerSecond: DEFAULT_MARQUEE_SPEED_PX_PER_SECOND,
  setPixelsPerSecond: () => undefined,
});

export function HomepageMarqueeSpeedProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [pixelsPerSecond, setPixelsPerSecond] = useState(
    DEFAULT_MARQUEE_SPEED_PX_PER_SECOND,
  );
  const value = useMemo(
    () => ({ pixelsPerSecond, setPixelsPerSecond }),
    [pixelsPerSecond],
  );

  return (
    <MarqueeSpeedContext.Provider value={value}>
      {children}
    </MarqueeSpeedContext.Provider>
  );
}

export function ProductMarquee({
  section = "popular_marquee",
  title = "محصولات پرطرفدار",
  fallbackToLatestProducts = true,
}: ProductMarqueeProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [durationSeconds, setDurationSeconds] = useState(
    ORIGINAL_MARQUEE_DURATION_SECONDS,
  );
  const trackRef = useRef<HTMLDivElement>(null);
  const { pixelsPerSecond, setPixelsPerSecond } =
    useContext(MarqueeSpeedContext);
  const isSpeedReference = section === "popular_marquee";

  useEffect(() => {
    let isMounted = true;

    async function loadProducts() {
      try {
        const sections = normalizeHomepageSections(await getHomepageSections());
        const homepageProducts = getHomepageSectionProducts(
          sections,
          section,
        );

        if (isMounted) {
          if (homepageProducts.length > 0) {
            setProducts(homepageProducts);
            return;
          }

          if (!fallbackToLatestProducts) {
            setProducts([]);
            return;
          }

          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 12,
          });
          setProducts(response);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error(`${section} marquee API error:`, error);
        }

        if (!fallbackToLatestProducts) {
          if (isMounted) {
            setProducts([]);
          }
          return;
        }

        try {
          const response = await getProducts({
            ordering: "-created_at",
            page: 1,
            page_size: 12,
          });

          if (isMounted) {
            setProducts(response);
          }
        } catch (fallbackError) {
          if (process.env.NODE_ENV !== "production") {
            console.error(`${section} marquee fallback API error:`, fallbackError);
          }
        }
      }
    }

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, [fallbackToLatestProducts, section]);

  const marqueeProducts = useMemo(() => {
    if (products.length === 0) {
      return [];
    }

    return [...products, ...products];
  }, [products]);

  useLayoutEffect(() => {
    const track = trackRef.current;

    if (!track || marqueeProducts.length === 0) {
      return;
    }

    const marqueeTrack = track;

    function updateMarqueeSpeed() {
      const travelDistance = marqueeTrack.scrollWidth / 2;

      if (travelDistance <= 0) {
        return;
      }

      if (isSpeedReference) {
        const measuredSpeed =
          travelDistance / ORIGINAL_MARQUEE_DURATION_SECONDS;
        setPixelsPerSecond(measuredSpeed);
        setDurationSeconds(ORIGINAL_MARQUEE_DURATION_SECONDS);
        return;
      }

      setDurationSeconds(Math.max(travelDistance / pixelsPerSecond, 1));
    }

    updateMarqueeSpeed();

    const resizeObserver = new ResizeObserver(updateMarqueeSpeed);
    resizeObserver.observe(marqueeTrack);

    return () => resizeObserver.disconnect();
  }, [
    isSpeedReference,
    marqueeProducts.length,
    pixelsPerSecond,
    setPixelsPerSecond,
  ]);

  if (marqueeProducts.length === 0) {
    return null;
  }

  return (
    <section
      className="pb-12 pt-1 sm:pb-14 sm:pt-2"
      aria-labelledby={`${section}-title`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-[2.5rem] border border-white/70 bg-white/78 p-4 shadow-card backdrop-blur dark:border-white/10 sm:p-6">
          <div className="mb-5 flex items-center justify-between gap-4 px-2">
            <p
              className="text-[0.9375rem] font-black text-ink sm:text-[1.0625rem]"
              id={`${section}-title`}
            >
              {title}
            </p>
            <Link className="text-[0.8125rem] font-bold text-coral" href="/products">
              مشاهده همه
            </Link>
          </div>
          <div className="group relative overflow-hidden">
            <div
              className="flex w-max animate-marquee-rtl gap-5 will-change-transform sm:gap-6"
              ref={trackRef}
              style={
                {
                  "--marquee-duration": `${durationSeconds}s`,
                } as CSSProperties
              }
            >
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
        <span
          className="block truncate text-[0.8125rem] font-black leading-6 text-ink sm:text-[0.9375rem] sm:leading-7"
          title={product.name}
        >
          {product.name}
        </span>
        <span className="mt-2 block text-[0.8125rem] font-black text-coral sm:text-[0.9375rem]">
          {formatToman(getProductPrice(product))}
        </span>
      </span>
    </Link>
  );
}
