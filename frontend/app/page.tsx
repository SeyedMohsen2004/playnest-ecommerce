import { BenefitsSection } from "@/components/home/benefits-section";
import { FeaturedCategories } from "@/components/home/featured-categories";
import { FeaturedProducts } from "@/components/home/featured-products";
import { HeroSection } from "@/components/home/hero-section";
import { NewsletterSection } from "@/components/home/newsletter-section";
import { ProductMarquee } from "@/components/home/product-marquee";

export default function Home() {
  return (
    <>
      <HeroSection />
      <ProductMarquee />
      <FeaturedCategories />
      <FeaturedProducts />
      <BenefitsSection />
      <NewsletterSection />
    </>
  );
}
