import type { NextConfig } from "next";

const internalApiBaseUrl = process.env.INTERNAL_API_BASE_URL?.replace(
  /\/+$/,
  "",
);

const internalApiOrigin = internalApiBaseUrl
  ? new URL(internalApiBaseUrl).origin
  : null;

const nextConfig: NextConfig = {
  output: "standalone",
  skipTrailingSlashRedirect: true,

  async rewrites() {
    if (!internalApiBaseUrl || !internalApiOrigin) {
      return [];
    }

    return [
      {
        source: "/api/v1/:path*/",
        destination: `${internalApiBaseUrl}/:path*/`,
      },
      {
        source: "/media/:path*",
        destination: `${internalApiOrigin}/media/:path*`,
      },
    ];
  },
};

export default nextConfig;
