import { API_BASE_URL } from "@/lib/api/client";
import type { Product as MockProduct } from "@/types";
import type {
  Brand as ApiBrand,
  Category as ApiCategory,
  Product as ApiProduct,
  ProductImage,
} from "@/types/api";

export type ProductSource = MockProduct | ApiProduct;

const ageGroupLabels: Record<ApiProduct["age_group"], string> = {
  "0_2": "۰ تا ۲ سال",
  "3_5": "۳ تا ۵ سال",
  "6_8": "۶ تا ۸ سال",
  "9_12": "۹ تا ۱۲ سال",
  "12_plus": "۱۲ سال به بالا",
};

export const genderLabels: Record<ApiProduct["gender"], string> = {
  unisex: "مناسب همه",
  boy: "مناسب پسران",
  girl: "مناسب دختران",
};

export function isApiProduct(product: ProductSource): product is ApiProduct {
  return "id" in product;
}

function isApiCategory(value: ApiProduct["category"]): value is ApiCategory {
  return typeof value === "object" && value !== null;
}

function isApiBrand(value: ApiProduct["brand"]): value is ApiBrand {
  return typeof value === "object" && value !== null;
}

function toNumber(value: number | string | null | undefined) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : 0;
}

export function getProductCategoryName(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.category;
  }

  if (product.category_detail) {
    return product.category_detail.name;
  }

  if (isApiCategory(product.category)) {
    return product.category.name;
  }

  return String(product.category || "دسته‌بندی");
}

export function getProductCategoryKey(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.categorySlug;
  }

  if (product.category_detail) {
    return product.category_detail.slug;
  }

  if (isApiCategory(product.category)) {
    return product.category.slug;
  }

  return String(product.category);
}

export function getProductBrandName(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.brand;
  }

  if (product.brand_detail) {
    return product.brand_detail.name;
  }

  if (isApiBrand(product.brand)) {
    return product.brand.name;
  }

  return product.brand ? String(product.brand) : "بدون برند";
}

export function getProductAgeGroup(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.ageGroup;
  }

  return ageGroupLabels[product.age_group];
}

export function getProductGender(product: ProductSource) {
  if (!isApiProduct(product)) {
    return "مناسب همه";
  }

  return genderLabels[product.gender];
}

export function getProductPrice(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.price;
  }

  return toNumber(product.final_price || product.discount_price || product.price);
}

export function getProductOldPrice(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.oldPrice;
  }

  return product.discount_price ? product.price : undefined;
}

export function getProductShortDescription(product: ProductSource) {
  return isApiProduct(product)
    ? product.short_description || product.description
    : product.shortDescription;
}

export function getProductDescription(product: ProductSource) {
  return product.description;
}

export function getProductRating(product: ProductSource) {
  if (!isApiProduct(product)) {
    return null;
  }

  return product.average_rating === null || product.average_rating === undefined
    ? null
    : toNumber(product.average_rating);
}

export function getProductReviewCount(product: ProductSource) {
  return isApiProduct(product) ? product.review_count || 0 : 0;
}

export function getProductStock(product: ProductSource) {
  return product.stock;
}

export function getProductIsInStock(product: ProductSource) {
  return isApiProduct(product) ? product.is_in_stock : product.stock > 0;
}

export function getProductBadge(product: ProductSource) {
  if (!isApiProduct(product)) {
    return product.badge;
  }

  if (!product.is_in_stock) {
    return "ناموجود";
  }

  return product.is_featured ? "ویژه" : "محصول";
}

export function getProductImageClass(product: ProductSource) {
  return isApiProduct(product)
    ? "from-sky-100 via-rose-50 to-amber-100"
    : product.imageClass;
}

function normalizeImageUrl(imageUrl?: string | null) {
  if (!imageUrl) {
    return null;
  }

  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }

  try {
    const apiOrigin = new URL(API_BASE_URL).origin;
    return `${apiOrigin}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
  } catch {
    return imageUrl;
  }
}

function getMainImage(product: ApiProduct): ProductImage | null {
  return (
    product.images?.find((image) => image.is_main) ||
    product.images?.[0] ||
    product.main_image ||
    null
  );
}

export function getProductImageUrl(product: ProductSource) {
  if (!isApiProduct(product)) {
    return null;
  }

  return normalizeImageUrl(getMainImage(product)?.image);
}

export function getProductImages(product: ProductSource) {
  if (!isApiProduct(product)) {
    return [];
  }

  const images =
    product.images && product.images.length > 0
      ? product.images
      : product.main_image
        ? [product.main_image]
        : [];

  return images
    .map((image) => ({
      ...image,
      image: normalizeImageUrl(image.image) || "",
    }))
    .filter((image) => image.image);
}
