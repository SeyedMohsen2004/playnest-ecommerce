import type { MetadataRoute } from "next";

const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000")
  .replace(/\/+$/, "");

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

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return publicRoutes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: now,
    changeFrequency: route === "" || route === "/products" ? "daily" : "monthly",
    priority: route === "" ? 1 : route === "/products" ? 0.9 : 0.6,
  }));
}
