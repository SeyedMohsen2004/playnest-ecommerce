import type { MetadataRoute } from "next";

import { API_BASE_URL } from "@/lib/api/client";
import { absoluteUrl } from "@/lib/seo";
import type { PaginatedResponse, Product } from "@/types/api";

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

async function getProductRoutes(): Promise<MetadataRoute.Sitemap> {
  try {
    const url = new URL(`${API_BASE_URL}/products/`);
    url.searchParams.set("page", "1");
    url.searchParams.set("page_size", "48");
    url.searchParams.set("ordering", "-created_at");

    const response = await fetch(url.toString(), {
      headers: {
        Accept: "application/json",
      },
      next: {
        revalidate,
      },
    });

    if (!response.ok) {
      return [];
    }

    const productsResponse = (await response.json()) as
      | Product[]
      | PaginatedResponse<Product>;
    const products = Array.isArray(productsResponse)
      ? productsResponse
      : productsResponse.results;

    return products
      .filter((product) => product.is_active && product.slug)
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
