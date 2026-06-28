import { BenefitsSection } from "@/components/home/benefits-section";
import { FeaturedProducts } from "@/components/home/featured-products";
import { HeroSection } from "@/components/home/hero-section";
import { LatestProductsCarousel } from "@/components/home/latest-products-carousel";
import { NewsletterSection } from "@/components/home/newsletter-section";
import { ProductMarquee } from "@/components/home/product-marquee";

export default function Home() {
  return (
    <>
      <HeroSection />
      <ProductMarquee />
      <LatestProductsCarousel />
      <FeaturedProducts />
      <BenefitsSection />
      <NewsletterSection />
    </>
  );
}
