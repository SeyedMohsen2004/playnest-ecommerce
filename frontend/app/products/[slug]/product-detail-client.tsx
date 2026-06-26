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
import { useEffect, useMemo, useState } from "react";

import { ProductCartActions } from "@/components/product/product-cart-actions";
import { ProductCard } from "@/components/product/product-card";
import { useAuth } from "@/components/providers/auth-provider";
import { PriceText } from "@/components/shared/price-text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  getProductBySlug,
  getProductReviews,
  getProducts,
} from "@/lib/api/products";
import { toPersianDigits } from "@/lib/format";
import {
  getProductAgeGroup,
  getProductBadge,
  getProductBrandName,
  getProductCategoryKey,
  getProductCategoryName,
  getProductDescription,
  getProductGender,
  getProductImageClass,
  getProductImageUrl,
  getProductImages,
  getProductIsInStock,
  getProductOldPrice,
  getProductPrice,
  getProductRating,
  getProductReviewCount,
  getProductShortDescription,
  getProductStock,
} from "@/lib/product-display";
import { cn } from "@/lib/utils";
import type { Product, ProductReview } from "@/types/api";

const productBenefits: { label: string; icon: LucideIcon }[] = [
  { label: "ارسال سفارش", icon: Truck },
  { label: "کیفیت و اصالت بررسی‌شده", icon: ShieldCheck },
  { label: "بسته‌بندی مناسب هدیه", icon: PackageCheck },
  { label: "مناسب دورهمی و تمرین ذهن", icon: Sparkles },
];

type ProductState = {
  product: Product | null;
  isLoading: boolean;
};

export function ProductDetailClient({ slug }: { slug: string }) {
  const { isAuthenticated } = useAuth();
  const [{ product, isLoading }, setProductState] = useState<ProductState>({
    product: null,
    isLoading: true,
  });
  const [relatedProducts, setRelatedProducts] = useState<Product[]>([]);
  const [reviews, setReviews] = useState<ProductReview[]>([]);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [slug]);

  useEffect(() => {
    let isMounted = true;

    async function loadProduct() {
      setProductState({ product: null, isLoading: true });
      setRelatedProducts([]);
      setReviews([]);
      setSelectedImage(null);

      try {
        const apiProduct = await getProductBySlug(slug);
        const galleryImages = getProductImages(apiProduct);
        const initialImage = galleryImages[0]?.image || getProductImageUrl(apiProduct);

        if (!isMounted) {
          return;
        }

        setProductState({ product: apiProduct, isLoading: false });
        setSelectedImage(initialImage);

        const [productsResult, reviewsResult] = await Promise.allSettled([
          getProducts(),
          getProductReviews(slug),
        ]);

        if (!isMounted) {
          return;
        }

        if (productsResult.status === "fulfilled") {
          setRelatedProducts(
            buildRelatedProducts(apiProduct, productsResult.value),
          );
        } else if (process.env.NODE_ENV !== "production") {
          console.error("Related products API error:", productsResult.reason);
        }

        if (reviewsResult.status === "fulfilled") {
          setReviews(reviewsResult.value);
        } else if (process.env.NODE_ENV !== "production") {
          console.error("Product reviews API error:", reviewsResult.reason);
        }
      } catch (error) {
        if (process.env.NODE_ENV !== "production") {
          console.error("Product detail API error:", error);
        }

        if (isMounted) {
          setProductState({ product: null, isLoading: false });
        }
      }
    }

    loadProduct();

    return () => {
      isMounted = false;
    };
  }, [slug]);

  const galleryImages = useMemo(
    () => (product ? getProductImages(product) : []),
    [product],
  );

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

  const imageClass = getProductImageClass(product);
  const mainImageUrl =
    selectedImage || galleryImages[0]?.image || getProductImageUrl(product);
  const isInStock = getProductIsInStock(product);
  const rating = getProductRating(product);
  const reviewCount = reviews.length || getProductReviewCount(product);

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
            {mainImageUrl ? (
              <div
                aria-label={product.name}
                className="absolute inset-0 bg-cover bg-center"
                role="img"
                style={{ backgroundImage: `url("${mainImageUrl}")` }}
              />
            ) : (
              <div className="absolute inset-x-12 top-28 h-48 rotate-6 rounded-[3rem] bg-white/55 shadow-soft" />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-ink/25 via-transparent to-transparent" />
            <Badge className="absolute right-6 top-6 bg-white/90 text-coral">
              {getProductBadge(product)}
            </Badge>
          </div>

          {galleryImages.length > 0 ? (
            <div className="mt-4 grid grid-cols-4 gap-3">
              {galleryImages.map((image) => {
                const isActive = image.image === mainImageUrl;

                return (
                  <button
                    aria-label={`نمایش تصویر ${image.alt_text || product.name}`}
                    className={cn(
                      "h-24 overflow-hidden rounded-3xl bg-gradient-to-br ring-offset-2 transition",
                      imageClass,
                      isActive
                        ? "opacity-100 ring-2 ring-coral"
                        : "opacity-70 hover:opacity-100",
                    )}
                    key={image.id}
                    onClick={() => setSelectedImage(image.image)}
                    type="button"
                  >
                    <span
                      aria-hidden="true"
                      className="block h-full w-full bg-cover bg-center"
                      style={{ backgroundImage: `url("${image.image}")` }}
                    />
                  </button>
                );
              })}
            </div>
          ) : null}
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
          <div className="mt-5 flex flex-wrap items-center gap-2 text-sm font-bold text-ink/55">
            {reviewCount > 0 && rating !== null ? (
              <>
                <Star className="size-5 fill-current text-amber-500" />
                <span className="text-amber-500">
                  {toPersianDigits(rating.toFixed(1))} از ۵
                </span>
                <span className="text-ink/35">|</span>
                <span>{toPersianDigits(reviewCount)} دیدگاه</span>
              </>
            ) : (
              <span>بدون نظر</span>
            )}
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

          <ProductCartActions isInStock={isInStock} productId={product.id} />
        </section>
      </div>

      <section className="mt-12 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-black text-ink">توضیحات محصول</h2>
          <p className="mt-4 whitespace-pre-line leading-8 text-ink/65">
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
        {reviews.length > 0 ? (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {reviews.map((review) => (
              <div className="rounded-3xl bg-cream p-5" key={review.id}>
                <div className="flex items-center gap-1 text-amber-500">
                  {Array.from({ length: review.rating }).map((_, index) => (
                    <Star className="size-4 fill-current" key={index} />
                  ))}
                </div>
                <p className="mt-3 text-sm font-black text-ink">
                  {review.user_name || "کاربر IpakToys"}
                </p>
                <p className="mt-3 text-sm leading-7 text-ink/65">
                  {review.comment || "بدون متن"}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-3xl bg-cream p-5 text-sm leading-7 text-ink/65">
            <p className="font-bold">هنوز نظری برای این محصول ثبت نشده است.</p>
            {!isAuthenticated ? (
              <p className="mt-2">برای ثبت نظر ابتدا وارد حساب کاربری شوید.</p>
            ) : (
              <p className="mt-2">
                امکان ثبت نظر از پنل کاربری در مرحله بعدی فعال می‌شود.
              </p>
            )}
          </div>
        )}
      </section>

      {relatedProducts.length > 0 ? (
        <section className="mt-12">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-black text-ink">محصولات مرتبط</h2>
            <Link className="text-sm font-bold text-coral" href="/products">
              مشاهده همه
            </Link>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {relatedProducts.map((item) => (
              <ProductCard key={item.slug} product={item} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function buildRelatedProducts(product: Product, products: Product[]) {
  const categoryKey = getProductCategoryKey(product);
  const candidates = products.filter((item) => item.slug !== product.slug);
  const sameCategory = candidates.filter(
    (item) => getProductCategoryKey(item) === categoryKey,
  );
  const otherProducts = candidates.filter(
    (item) => !sameCategory.some((related) => related.slug === item.slug),
  );

  return [...sameCategory, ...otherProducts].slice(0, 3);
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
