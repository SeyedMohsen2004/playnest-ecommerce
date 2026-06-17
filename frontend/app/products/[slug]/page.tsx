import { Heart, ShieldCheck, Star, Truck } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ProductCard } from "@/components/product/product-card";
import { PriceText } from "@/components/shared/price-text";
import { QuantitySelector } from "@/components/shared/quantity-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { products } from "@/lib/mock-data";

const formatter = new Intl.NumberFormat("fa-IR");

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = products.find((item) => item.slug === slug);

  if (!product) {
    notFound();
  }

  const relatedProducts = products
    .filter(
      (item) =>
        item.slug !== product.slug && item.categorySlug === product.categorySlug,
    )
    .slice(0, 3);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid gap-10 lg:grid-cols-2 lg:items-start">
        <section>
          <div
            className={`relative min-h-[28rem] rounded-[2.5rem] bg-gradient-to-br ${product.imageClass} p-6 shadow-soft`}
          >
            <Badge className="absolute right-6 top-6 bg-white/85 text-coral">
              {product.badge}
            </Badge>
            <div className="absolute inset-x-12 top-28 h-48 rotate-6 rounded-[3rem] bg-white/55 shadow-soft" />
          </div>
          <div className="mt-4 grid grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((item) => (
              <div
                className={`h-24 rounded-3xl bg-gradient-to-br ${product.imageClass} opacity-${item === 1 ? "100" : "70"}`}
                key={item}
              />
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <Badge>{product.category}</Badge>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
              {product.stock > 0 ? "موجود در انبار" : "ناموجود"}
            </span>
          </div>
          <h1 className="mt-5 text-4xl font-black leading-tight text-ink">
            {product.name}
          </h1>
          <p className="mt-4 text-sm leading-7 text-ink/60">
            {product.shortDescription}
          </p>
          <div className="mt-5 flex items-center gap-2 text-sm font-bold text-amber-500">
            <Star className="size-5 fill-current" />
            {formatter.format(product.rating)} از ۵
            <span className="text-ink/35">|</span>
            <span className="text-ink/55">۱۲ دیدگاه</span>
          </div>
          <PriceText
            amount={product.price}
            className="mt-6"
            oldAmount={product.oldPrice}
          />

          <dl className="mt-6 grid gap-3 rounded-3xl bg-cream p-5 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-bold text-ink/45">برند</dt>
              <dd className="mt-1 font-black text-ink">{product.brand}</dd>
            </div>
            <div>
              <dt className="font-bold text-ink/45">رده سنی</dt>
              <dd className="mt-1 font-black text-ink">{product.ageGroup}</dd>
            </div>
          </dl>

          <div className="mt-7 flex flex-col gap-4 sm:flex-row sm:items-center">
            <QuantitySelector />
            <Button className="flex-1" variant="coral">
              افزودن به سبد خرید
            </Button>
            <Button variant="outline">
              <Heart className="size-5" />
              علاقه‌مندی
            </Button>
          </div>
        </section>
      </div>

      <section className="mt-12 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-black text-ink">توضیحات محصول</h2>
          <p className="mt-4 leading-8 text-ink/65">{product.description}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          {[
            ["ارسال سریع", Truck],
            ["کیفیت و ایمنی بررسی‌شده", ShieldCheck],
          ].map(([label, Icon]) => (
            <div
              className="flex items-center gap-3 rounded-3xl bg-white p-5 shadow-sm"
              key={String(label)}
            >
              <span className="flex size-12 items-center justify-center rounded-2xl bg-mint/25 text-emerald-700">
                <Icon className="size-6" />
              </span>
              <span className="font-black text-ink">{String(label)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12 rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-black text-ink">دیدگاه خریداران</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {["کیفیت خیلی خوبی داشت و بسته‌بندی هم عالی بود.", "برای هدیه تولد خریدم و کودک خیلی خوشحال شد."].map(
            (review) => (
              <div className="rounded-3xl bg-cream p-5" key={review}>
                <div className="flex items-center gap-1 text-amber-500">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <Star className="size-4 fill-current" key={index} />
                  ))}
                </div>
                <p className="mt-3 text-sm leading-7 text-ink/65">{review}</p>
              </div>
            ),
          )}
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
          {(relatedProducts.length ? relatedProducts : products.slice(0, 3)).map(
            (item) => (
              <ProductCard key={item.slug} product={item} />
            ),
          )}
        </div>
      </section>
    </div>
  );
}
