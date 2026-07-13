import type { MetadataRoute } from "next";

import { absoluteUrl, SITE_URL } from "@/lib/seo";
import type { PaginatedResponse } from "@/types/api";

const publicRoutes = [
  "",
  "/products",
  "/about",
  "/contact",
  "/terms",
  "/privacy",
  "/returns",
  "/shipping",
  "/shopping-guide",
];

export const revalidate = 3600;

const PRODUCT_SITEMAP_PAGE_SIZE = 48;
const PRODUCT_SITEMAP_MAX_PAGES = 20;
const SITEMAP_API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || `${SITE_URL}/api/v1`
).replace(/\/+$/, "");

type ProductSitemapItem = {
  slug?: string | null;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
};

function getProductsEndpoint(page: number) {
  const url = new URL(`${SITEMAP_API_BASE_URL}/products/`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("page_size", String(PRODUCT_SITEMAP_PAGE_SIZE));
  url.searchParams.set("ordering", "-created_at");
  return url;
}

async function fetchProductSitemapPage(page: number) {
  const response = await fetch(getProductsEndpoint(page).toString(), {
    headers: {
      Accept: "application/json",
    },
    next: {
      revalidate,
    },
  });

  if (!response.ok) {
    return {
      products: [],
      hasNextPage: false,
    };
  }

  const productsResponse = (await response.json()) as
    | ProductSitemapItem[]
    | PaginatedResponse<ProductSitemapItem>;

  if (Array.isArray(productsResponse)) {
    return {
      products: productsResponse,
      hasNextPage: false,
    };
  }

  return {
    products: productsResponse.results,
    hasNextPage: Boolean(productsResponse.next),
  };
}

async function getProductRoutes(): Promise<MetadataRoute.Sitemap> {
  try {
    const products: ProductSitemapItem[] = [];

    for (let page = 1; page <= PRODUCT_SITEMAP_MAX_PAGES; page += 1) {
      const { products: pageProducts, hasNextPage } =
        await fetchProductSitemapPage(page);
      products.push(...pageProducts);

      if (!hasNextPage) {
        break;
      }
    }

    const seenSlugs = new Set<string>();

    return products
      .filter((product) => product.is_active !== false && product.slug)
      .filter((product): product is ProductSitemapItem & { slug: string } => {
        if (!product.slug || seenSlugs.has(product.slug)) {
          return false;
        }

        seenSlugs.add(product.slug);
        return true;
      })
      .map((product) => ({
        url: absoluteUrl(`/products/${product.slug}`),
        lastModified: product.updated_at
          ? new Date(product.updated_at)
          : product.created_at
            ? new Date(product.created_at)
            : new Date(),
        changeFrequency: "weekly",
        priority: 0.8,
      }));
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.error("Sitemap products API error:", error);
    }

    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const staticRoutes: MetadataRoute.Sitemap = publicRoutes.map((route) => ({
    url: absoluteUrl(route || "/"),
    lastModified: now,
    changeFrequency: route === "" || route === "/products" ? "daily" : "monthly",
    priority: route === "" ? 1 : route === "/products" ? 0.9 : 0.6,
  }));

  return [...staticRoutes, ...(await getProductRoutes())];
}
