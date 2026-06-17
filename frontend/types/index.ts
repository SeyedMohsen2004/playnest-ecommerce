import type { LucideIcon } from "lucide-react";

export type Category = {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  color: string;
};

export type Product = {
  name: string;
  category: string;
  price: number;
  oldPrice?: number;
  badge: string;
  rating: number;
  imageClass: string;
};

export type Benefit = {
  title: string;
  description: string;
};
