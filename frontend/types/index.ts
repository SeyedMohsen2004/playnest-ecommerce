import type { LucideIcon } from "lucide-react";

export type Category = {
  slug: string;
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  color: string;
};

export type Brand = {
  slug: string;
  name: string;
};

export type Product = {
  slug: string;
  name: string;
  category: string;
  categorySlug: string;
  brand: string;
  brandSlug: string;
  ageGroup: string;
  price: number;
  oldPrice?: number;
  badge: string;
  rating: number;
  stock: number;
  description: string;
  shortDescription: string;
  imageClass: string;
};

export type Benefit = {
  title: string;
  description: string;
};

export type CartItem = {
  id: number;
  product: Product;
  quantity: number;
};

export type OrderStatus =
  | "pending"
  | "payment_failed"
  | "paid"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled";

export type Order = {
  id: number;
  status: OrderStatus;
  total: number;
  date: string;
  itemCount: number;
};
