import type { Metadata } from "next";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import "./globals.css";

const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000")
  .replace(/\/+$/, "");

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "IpakToys | فروشگاه بازی فکری و بردگیم",
    template: "%s | IpakToys",
  },
  description:
    "فروشگاه آنلاین بازی فکری، بردگیم، پازل و محصولات ساختنی برای خریدی ساده و مطمئن.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "IpakToys | فروشگاه بازی فکری و بردگیم",
    description:
      "خرید بازی فکری، بردگیم، پازل و محصولات ساختنی برای کودک، نوجوان و خانواده.",
    locale: "fa_IR",
    siteName: "IpakToys",
    type: "website",
    url: "/",
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
    const theme = storedTheme || (
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
    );
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.style.colorScheme = theme;
  } catch (_) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
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
