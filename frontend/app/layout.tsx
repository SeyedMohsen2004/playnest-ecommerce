import type { Metadata } from "next";
import Script from "next/script";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import {
  HOME_DESCRIPTION,
  HOME_TITLE,
  SEO_KEYWORDS,
  SITE_NAME,
  SITE_URL,
} from "@/lib/seo";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: HOME_TITLE,
    template: `%s | ${SITE_NAME}`,
  },
  description: HOME_DESCRIPTION,
  keywords: SEO_KEYWORDS,
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon-48x48.png", sizes: "48x48", type: "image/png" },
      { url: "/icon-96x96.png", sizes: "96x96", type: "image/png" },
      { url: "/icon-192x192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  robots: {
    index: true,
    follow: true,
  },
};

const themeScript = `
(() => {
  try {
    const storedTheme = localStorage.getItem("ipaktoys-theme");
    const theme = storedTheme === "light" || storedTheme === "dark"
      ? storedTheme
      : "dark";
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.style.colorScheme = theme;
  } catch (_) {}
})();
`;

const umamiScriptUrl = getUmamiScriptUrl(
  process.env.NEXT_PUBLIC_UMAMI_SCRIPT_URL,
);
const umamiWebsiteId = process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID?.trim();
const umamiDomains = process.env.NEXT_PUBLIC_UMAMI_DOMAINS?.split(",")
  .map((domain) => domain.trim())
  .filter(Boolean)
  .join(",");
const umamiPerformanceEnabled =
  process.env.NEXT_PUBLIC_UMAMI_ENABLE_PERFORMANCE?.trim().toLowerCase() ===
  "true";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        {umamiScriptUrl && umamiWebsiteId ? (
          <Script
            data-domains={umamiDomains || undefined}
            data-do-not-track="true"
            data-exclude-search="true"
            data-performance={umamiPerformanceEnabled ? "true" : undefined}
            data-website-id={umamiWebsiteId}
            id="umami-analytics"
            src={umamiScriptUrl}
            strategy="afterInteractive"
          />
        ) : null}
      </head>
      <body className="antialiased">
        <ThemeProvider>
          <AuthProvider>
            <SiteHeader />
            <main>{children}</main>
            <SiteFooter />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

function getUmamiScriptUrl(value: string | undefined) {
  if (!value?.trim()) {
    return null;
  }

  try {
    const url = new URL(value.trim());
    return url.protocol === "https:" || url.protocol === "http:"
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}
