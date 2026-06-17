import { Heart, ShoppingCart, Star } from "lucide-react";
import Link from "next/link";

import { PriceText } from "@/components/shared/price-text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Product } from "@/types";

const formatter = new Intl.NumberFormat("fa-IR");

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="group overflow-hidden rounded-3xl border border-ink/5 bg-white text-right shadow-sm transition hover:-translate-y-1 hover:shadow-soft">
      <Link href={`/products/${product.slug}`} className="block">
        <div
          className={cn(
            "relative flex h-52 items-center justify-center bg-gradient-to-br",
            product.imageClass,
          )}
        >
          <Badge className="absolute right-4 top-4 bg-white/85 text-coral">
            {product.badge}
          </Badge>
          <button
            type="button"
            className="absolute left-4 top-4 flex size-10 items-center justify-center rounded-full bg-white/85 text-ink shadow-sm transition hover:text-coral"
            aria-label={`افزودن ${product.name} به علاقه‌مندی‌ها`}
          >
            <Heart className="size-5" />
          </button>
          <div className="size-24 rotate-6 rounded-[2rem] bg-white/70 shadow-soft transition group-hover:rotate-12" />
        </div>
      </Link>

      <div className="p-5">
        <p className="text-xs font-bold uppercase tracking-wide text-ink/45">
          {product.category}
        </p>
        <Link href={`/products/${product.slug}`}>
          <h3 className="mt-2 min-h-14 text-lg font-black leading-7 text-ink transition hover:text-coral">
            {product.name}
          </h3>
        </Link>
        <div className="mt-3 flex items-center gap-1 text-sm font-bold text-amber-500">
          <Star className="size-4 fill-current" />
          {formatter.format(product.rating)}
        </div>
        <PriceText
          amount={product.price}
          className="mt-4"
          oldAmount={product.oldPrice}
        />
        <Button className="mt-5 w-full" variant="outline">
          <ShoppingCart className="size-4" />
          افزودن به سبد خرید
        </Button>
      </div>
    </article>
  );
}
