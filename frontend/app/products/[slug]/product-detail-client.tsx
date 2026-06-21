"use client";

import type { LucideIcon } from "lucide-react";
import {
  PackageCheck,
  ShieldCheck,
  Sparkles,
  Star,
  Truck,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { ProductCartActions } from "@/components/product/product-cart-actions";
import { ProductCard } from "@/components/product/product-card";
import { PriceText } from "@/components/shared/price-text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getProductBySlug } from "@/lib/api/products";
import { toPersianDigits } from "@/lib/format";
import { products as mockProducts } from "@/lib/mock-data";
import {
  getProductAgeGroup,
  getProductBadge,
  getProductBrandName,
  getProductCategoryKey,
  getProductCategoryName,
  getProductDescription,
  getProductGender,
  getProductImageClass,
  getProductImages,
  getProductImageUrl,
  getProductIsInStock,
  getProductOldPrice,
  getProductPrice,
  getProductRating,
  getProductReviewCount,
  getProductShortDescription,
  getProductStock,
  isApiProduct,
  type ProductSource,
} from "@/lib/product-display";
import { cn } from "@/lib/utils";

const productBenefits: { label: string; icon: LucideIcon }[] = [
  { label: "ارسال سریع", icon: Truck },
  { label: "کیفیت و اصالت بررسی‌شده", icon: ShieldCheck },
  { label: "بسته‌بندی مناسب هدیه", icon: PackageCheck },
  { label: "مناسب دورهمی و تمرین ذهن", icon: Sparkles },
];

type ProductState = {
  product: ProductSource | null;
  isLoading: boolean;
};

export function ProductDetailClient({ slug }: { slug: string }) {
  const [{ product, isLoading }, setProductState] = useState<ProductState>({
    product: null,
    isLoading: true,
  });

  useEffect(() => {
    let isMounted = true;

    async function loadProduct() {
      setProductState({ product: null, isLoading: true });

      try {
        const apiProduct = await getProductBySlug(slug);

        if (isMounted) {
          setProductState({ product: apiProduct, isLoading: false });
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Product detail API error:", error);
        }

        if (isMounted) {
          setProductState({
            product: mockProducts.find((item) => item.slug === slug) || null,
            isLoading: false,
          });
        }
      }
    }

    loadProduct();

    return () => {
      isMounted = false;
    };
  }, [slug]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
        <div className="rounded-[2.5rem] bg-white p-8 text-sm font-black text-ink/60 shadow-soft sm:p-12">
          در حال دریافت اطلاعات محصول...
        </div>
      </div>
    );
  }

  if (!product) {
    return <ProductNotFound />;
  }

  const imageUrl = getProductImageUrl(product);
  const imageClass = getProductImageClass(product);
  const galleryImages = getProductImages(product);
  const isInStock = getProductIsInStock(product);
  const rating = getProductRating(product);
  const reviewCount = getProductReviewCount(product);
  const relatedProducts = mockProducts
    .filter(
      (item) =>
        item.slug !== product.slug &&
        item.categorySlug === getProductCategoryKey(product),
    )
    .slice(0, 3);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
        <section>
          <div
            className={cn(
              "relative min-h-[28rem] overflow-hidden rounded-[2.5rem] bg-gradient-to-br p-6 shadow-soft",
              imageClass,
            )}
          >
            {imageUrl ? (
              <div
                aria-label={product.name}
                className="absolute inset-0 bg-cover bg-center"
                role="img"
                style={{ backgroundImage: `url("${imageUrl}")` }}
              />
            ) : (
              <div className="absolute inset-x-12 top-28 h-48 rotate-6 rounded-[3rem] bg-white/55 shadow-soft" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-ink/25 via-transparent to-transparent" />
            <Badge className="absolute right-6 top-6 bg-white/90 text-coral">
              {getProductBadge(product)}
            </Badge>
          </div>
          <div className="mt-4 grid grid-cols-4 gap-3">
            {(galleryImages.length
              ? galleryImages
              : Array.from({ length: 4 }, (_, index) => ({
                  id: index,
                  image: "",
                  alt_text: product.name,
                }))
            ).map((image, index) => (
              <div
                className={cn(
                  "h-24 overflow-hidden rounded-3xl bg-gradient-to-br",
                  imageClass,
                  index === 0 ? "opacity-100" : "opacity-70",
                )}
                key={image.id}
              >
                {image.image ? (
                  <div
                    aria-label={image.alt_text || product.name}
                    className="h-full w-full bg-cover bg-center"
                    role="img"
                    style={{ backgroundImage: `url("${image.image}")` }}
                  />
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge>{getProductCategoryName(product)}</Badge>
            <span
              className={cn(
                "rounded-full px-3 py-1 text-xs font-bold",
                isInStock
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-rose-100 text-rose-700",
              )}
            >
              {isInStock ? "موجود در انبار" : "ناموجود"}
            </span>
          </div>
          <h1 className="mt-5 text-4xl font-black leading-tight text-ink">
            {product.name}
          </h1>
          <p className="mt-4 text-sm leading-7 text-ink/60">
            {getProductShortDescription(product)}
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-2 text-sm font-bold text-amber-500">
            <Star className="size-5 fill-current" />
            {toPersianDigits(rating ? rating.toFixed(1) : "0")} از ۵
            <span className="text-ink/35">|</span>
            <span className="text-ink/55">
              {toPersianDigits(reviewCount)} دیدگاه
            </span>
          </div>
          <PriceText
            amount={getProductPrice(product)}
            className="mt-6"
            oldAmount={getProductOldPrice(product)}
          />

          <dl className="mt-6 grid gap-3 rounded-3xl bg-cream p-5 text-sm sm:grid-cols-2">
            <DetailMeta label="برند" value={getProductBrandName(product)} />
            <DetailMeta label="رده سنی" value={getProductAgeGroup(product)} />
            <DetailMeta label="گروه استفاده" value={getProductGender(product)} />
            <DetailMeta
              label="موجودی"
              value={`${toPersianDigits(getProductStock(product))} عدد`}
            />
          </dl>

          <ProductCartActions
            isInStock={isInStock}
            productId={isApiProduct(product) ? product.id : null}
          />
        </section>
      </div>

      <section className="mt-12 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-black text-ink">توضیحات محصول</h2>
          <p className="mt-4 leading-8 text-ink/65">
            {getProductDescription(product)}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          {productBenefits.map(({ label, icon: Icon }) => (
            <div
              className="flex items-center gap-3 rounded-3xl bg-white p-5 shadow-sm"
              key={label}
            >
              <span className="flex size-12 items-center justify-center rounded-2xl bg-mint/25 text-emerald-700">
                <Icon className="size-6" />
              </span>
              <span className="font-black text-ink">{label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12 rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-black text-ink">دیدگاه خریداران</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {[
            "کیفیت خیلی خوبی داشت و بسته‌بندی هم عالی بود.",
            "برای هدیه خریدیم و تجربه خرید راحتی داشتیم.",
          ].map((review) => (
            <div className="rounded-3xl bg-cream p-5" key={review}>
              <div className="flex items-center gap-1 text-amber-500">
                {Array.from({ length: 5 }).map((_, index) => (
                  <Star className="size-4 fill-current" key={index} />
                ))}
              </div>
              <p className="mt-3 text-sm leading-7 text-ink/65">{review}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-black text-ink">محصولات مرتبط</h2>
          <Link className="text-sm font-bold text-coral" href="/products">
            مشاهده همه
          </Link>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {(relatedProducts.length ? relatedProducts : mockProducts.slice(0, 3))
            .filter((item) => item.slug !== product.slug)
            .map((item) => (
              <ProductCard key={item.slug} product={item} />
            ))}
        </div>
      </section>
    </div>
  );
}

function ProductNotFound() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
      <div className="rounded-[2.5rem] bg-white p-8 shadow-soft sm:p-12">
        <div className="mx-auto flex size-20 items-center justify-center rounded-[2rem] bg-coral/10 text-coral">
          <PackageCheck className="size-10" />
        </div>
        <h1 className="mt-6 text-3xl font-black text-ink">
          محصولی پیدا نشد
        </h1>
        <p className="mx-auto mt-3 max-w-xl leading-8 text-ink/60">
          این محصول در حال حاضر در فروشگاه IpakToys موجود نیست یا آدرس آن تغییر
          کرده است.
        </p>
        <Button asChild className="mt-7" variant="coral">
          <Link href="/products">بازگشت به محصولات</Link>
        </Button>
      </div>
    </div>
  );
}

function DetailMeta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-bold text-ink/45">{label}</dt>
      <dd className="mt-1 font-black text-ink">{value}</dd>
    </div>
  );
}
