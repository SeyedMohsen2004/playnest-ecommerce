import type { Metadata } from "next";

import { ProductDetailClient } from "@/app/products/[slug]/product-detail-client";
import { getProductBySlug } from "@/lib/api/products";
import { getProductImageUrl } from "@/lib/product-display";
import {
  absoluteUrl,
  DEFAULT_DESCRIPTION,
  SITE_NAME,
  truncateMetaDescription,
} from "@/lib/seo";

type ProductDetailPageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({
  params,
}: ProductDetailPageProps): Promise<Metadata> {
  const { slug } = await params;

  try {
    const product = await getProductBySlug(slug);
    const title = `${product.name} | ${SITE_NAME}`;
    const description = truncateMetaDescription(
      product.short_description ||
        product.description ||
        `خرید ${product.name} از فروشگاه ایپک تویز`,
    );
    const productUrl = absoluteUrl(`/products/${product.slug}`);
    const imageUrl = getProductImageUrl(product);

    return {
      title: {
        absolute: title,
      },
      description,
      alternates: {
        canonical: productUrl,
      },
      openGraph: {
        title,
        description,
        url: productUrl,
        siteName: SITE_NAME,
        locale: "fa_IR",
        type: "website",
        images: imageUrl
          ? [
              {
                url: imageUrl,
                alt: product.name,
              },
            ]
          : undefined,
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        images: imageUrl ? [imageUrl] : undefined,
      },
      robots: {
        index: product.is_active,
        follow: product.is_active,
      },
    };
  } catch {
    return {
      title: {
        absolute: `محصول | ${SITE_NAME}`,
      },
      description: DEFAULT_DESCRIPTION,
      alternates: {
        canonical: absoluteUrl(`/products/${slug}`),
      },
    };
  }
}

export default async function ProductDetailPage({ params }: ProductDetailPageProps) {
  const { slug } = await params;

  return <ProductDetailClient slug={slug} />;
}
