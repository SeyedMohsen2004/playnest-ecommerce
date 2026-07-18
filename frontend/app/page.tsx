import type { Metadata } from "next";

import { BenefitsSection } from "@/components/home/benefits-section";
import { FeaturedProducts } from "@/components/home/featured-products";
import { HeroSection } from "@/components/home/hero-section";
import { LatestProductsCarousel } from "@/components/home/latest-products-carousel";
import { NewsletterSection } from "@/components/home/newsletter-section";
import {
  HomepageMarqueeSpeedProvider,
  ProductMarquee,
} from "@/components/home/product-marquee";
import {
  absoluteUrl,
  HOME_DESCRIPTION,
  HOME_OG_TITLE,
  HOME_TITLE,
  SITE_NAME,
} from "@/lib/seo";

export const metadata: Metadata = {
  title: {
    absolute: HOME_TITLE,
  },
  description: HOME_DESCRIPTION,
  alternates: {
    canonical: absoluteUrl("/"),
  },
  openGraph: {
    title: HOME_OG_TITLE,
    description: HOME_DESCRIPTION,
    locale: "fa_IR",
    siteName: SITE_NAME,
    type: "website",
    url: absoluteUrl("/"),
    images: [
      {
        url: absoluteUrl("/images/brand/ipacktoys-logo.png"),
        alt: "لوگوی ایپک تویز",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: HOME_TITLE,
    description: HOME_DESCRIPTION,
    images: [absoluteUrl("/images/brand/ipacktoys-logo.png")],
  },
};

export default function Home() {
  return (
    <HomepageMarqueeSpeedProvider>
      <HeroSection />
      <ProductMarquee />
      <LatestProductsCarousel />
      <ProductMarquee
        fallbackToLatestProducts={false}
        section="board_games"
        title="برد گیم‌ها"
      />
      <ProductMarquee
        fallbackToLatestProducts={false}
        section="construction"
        title="ساختنی‌ها"
      />
      <FeaturedProducts />
      <ProductMarquee
        fallbackToLatestProducts={false}
        section="educational"
        title="آموزشی"
      />
      <BenefitsSection />
      <NewsletterSection />
    </HomepageMarqueeSpeedProvider>
  );
}
