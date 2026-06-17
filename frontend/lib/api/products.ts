import { apiClient } from "@/lib/api/client";
import type { Brand, Category, PaginatedResponse, Product } from "@/types/api";

export type ProductQueryParams = {
  search?: string;
  category?: string | number;
  brand?: string | number;
  age_group?: Product["age_group"];
  ordering?: "price" | "-price" | "created_at" | "-created_at";
  page?: number;
};

type ListResponse<T> = T[] | PaginatedResponse<T>;

export function getProducts(params?: ProductQueryParams) {
  return apiClient.get<ListResponse<Product>>("/products/", { params });
}

export function getProductBySlug(slug: string) {
  return apiClient.get<Product>(`/products/${slug}/`);
}

export function getCategories() {
  return apiClient.get<ListResponse<Category>>("/categories/");
}

export function getBrands() {
  return apiClient.get<ListResponse<Brand>>("/brands/");
}
