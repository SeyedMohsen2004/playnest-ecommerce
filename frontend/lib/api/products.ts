import { apiClient } from "@/lib/api/client";
import type {
  Brand,
  Category,
  PaginatedResponse,
  Product,
  ProductReview,
} from "@/types/api";

export type ProductQueryParams = {
  search?: string;
  category?: string | number;
  brand?: string | number;
  age_group?: Product["age_group"];
  ordering?: "price" | "-price" | "created_at" | "-created_at";
  page?: number;
  page_size?: number;
};

type ListResponse<T> = T[] | PaginatedResponse<T>;

function normalizeListResponse<T>(response: ListResponse<T>): T[] {
  return Array.isArray(response) ? response : response.results;
}

function normalizePaginatedResponse<T>(
  response: ListResponse<T>,
): PaginatedResponse<T> {
  if (Array.isArray(response)) {
    return {
      count: response.length,
      next: null,
      previous: null,
      results: response,
    };
  }

  return response;
}

export function getProducts(params?: ProductQueryParams) {
  return apiClient
    .get<ListResponse<Product>>("/products/", { params })
    .then(normalizeListResponse);
}

export function getProductsPage(params?: ProductQueryParams) {
  return apiClient
    .get<ListResponse<Product>>("/products/", { params })
    .then(normalizePaginatedResponse);
}

export function getProductBySlug(slug: string) {
  return apiClient.get<Product>(`/products/${slug}/`);
}

export function getProductReviews(slug: string) {
  return apiClient
    .get<ListResponse<ProductReview>>(`/products/${slug}/reviews/`)
    .then(normalizeListResponse);
}

export function getCategories() {
  return apiClient
    .get<ListResponse<Category>>("/categories/")
    .then(normalizeListResponse);
}

export function getBrands() {
  return apiClient
    .get<ListResponse<Brand>>("/brands/")
    .then(normalizeListResponse);
}
