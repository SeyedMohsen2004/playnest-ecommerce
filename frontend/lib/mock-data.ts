import {
  Blocks,
  Brain,
  Car,
  GraduationCap,
  Heart,
  Puzzle,
} from "lucide-react";

import type { Benefit, Category, Product } from "@/types";

export const categories: Category[] = [
  {
    title: "Building Toys",
    description: "Creative blocks, magnetic tiles, and construction kits.",
    href: "#categories",
    icon: Blocks,
    color: "bg-sunshine/25 text-amber-700",
  },
  {
    title: "Dolls",
    description: "Soft friends, fashion dolls, and pretend-play favorites.",
    href: "#categories",
    icon: Heart,
    color: "bg-coral/20 text-rose-700",
  },
  {
    title: "Toy Cars",
    description: "Racers, tracks, metal cars, and remote-control fun.",
    href: "#categories",
    icon: Car,
    color: "bg-skysoft text-sky-700",
  },
  {
    title: "Learning Toys",
    description: "Early learning, science kits, alphabet cards, and more.",
    href: "#categories",
    icon: GraduationCap,
    color: "bg-mint/25 text-emerald-700",
  },
  {
    title: "Puzzles",
    description: "Brainy games and family-friendly puzzle challenges.",
    href: "#categories",
    icon: Puzzle,
    color: "bg-violet-100 text-violet-700",
  },
  {
    title: "Baby & Toddler",
    description: "Safe sensory toys for curious little hands.",
    href: "#categories",
    icon: Brain,
    color: "bg-orange-100 text-orange-700",
  },
];

export const featuredProducts: Product[] = [
  {
    name: "Rainbow Building Blocks",
    category: "Building Toys",
    price: 2450000,
    oldPrice: 2890000,
    badge: "Best seller",
    rating: 4.9,
    imageClass: "from-amber-200 via-orange-100 to-rose-100",
  },
  {
    name: "Soft Cuddle Doll",
    category: "Dolls",
    price: 720000,
    badge: "New",
    rating: 4.8,
    imageClass: "from-rose-200 via-pink-100 to-purple-100",
  },
  {
    name: "Remote Control Racer",
    category: "Toy Cars",
    price: 2150000,
    oldPrice: 2390000,
    badge: "Offer",
    rating: 4.7,
    imageClass: "from-sky-200 via-cyan-100 to-blue-100",
  },
  {
    name: "World Map Puzzle",
    category: "Puzzles",
    price: 650000,
    badge: "Family pick",
    rating: 4.9,
    imageClass: "from-emerald-200 via-lime-100 to-yellow-100",
  },
];

export const benefits: Benefit[] = [
  {
    title: "Safe toys",
    description: "Curated products with child-friendly materials and age guidance.",
  },
  {
    title: "Fast delivery",
    description: "Reliable shipping options designed for busy families.",
  },
  {
    title: "Easy returns",
    description: "Simple return flows for a stress-free shopping experience.",
  },
  {
    title: "Secure checkout",
    description: "A payment-ready architecture with verified order lifecycles.",
  },
];
