import {
  Blocks,
  Brain,
  Car,
  GraduationCap,
  Heart,
  Puzzle,
} from "lucide-react";

import type { Benefit, Brand, CartItem, Category, Order, Product } from "@/types";

export const categories: Category[] = [
  {
    slug: "building-toys",
    title: "لگو و ساختنی",
    description: "لگو، آجرهای رنگی، کاشی مغناطیسی و بازی‌های ساختنی.",
    href: "/products?category=building-toys",
    icon: Blocks,
    color: "bg-sunshine/25 text-amber-700",
  },
  {
    slug: "dolls",
    title: "عروسک",
    description: "عروسک‌های نرم، فانتزی و دوست‌داشتنی برای بازی‌های خیالی.",
    href: "/products?category=dolls",
    icon: Heart,
    color: "bg-coral/20 text-rose-700",
  },
  {
    slug: "toy-cars",
    title: "ماشین اسباب‌بازی",
    description: "ماشین فلزی، پیست مسابقه و خودروهای کنترلی هیجان‌انگیز.",
    href: "/products?category=toy-cars",
    icon: Car,
    color: "bg-skysoft text-sky-700",
  },
  {
    slug: "educational",
    title: "آموزشی",
    description: "کارت آموزشی، بازی علمی و ابزارهای یادگیری کودکانه.",
    href: "/products?category=educational",
    icon: GraduationCap,
    color: "bg-mint/25 text-emerald-700",
  },
  {
    slug: "puzzles",
    title: "فکری و پازل",
    description: "پازل، بازی فکری و سرگرمی‌های خانوادگی برای ذهن‌های کنجکاو.",
    href: "/products?category=puzzles",
    icon: Puzzle,
    color: "bg-violet-100 text-violet-700",
  },
  {
    slug: "baby-toddler",
    title: "نوزاد و خردسال",
    description: "اسباب‌بازی‌های ایمن و حسی برای دست‌های کوچک و کنجکاو.",
    href: "/products?category=baby-toddler",
    icon: Brain,
    color: "bg-orange-100 text-orange-700",
  },
];

export const brands: Brand[] = [
  { slug: "lego", name: "LEGO" },
  { slug: "mattel", name: "Mattel" },
  { slug: "hasbro", name: "Hasbro" },
  { slug: "fisher-price", name: "Fisher Price" },
  { slug: "playnest", name: "PlayNest" },
];

export const ageGroups = [
  "۰ تا ۲ سال",
  "۳ تا ۵ سال",
  "۶ تا ۸ سال",
  "۹ تا ۱۲ سال",
  "۱۲ سال به بالا",
];

export const products: Product[] = [
  {
    slug: "lego-classic-box",
    name: "بلوک‌های ساختنی رنگین‌کمان",
    category: "لگو و ساختنی",
    categorySlug: "building-toys",
    brand: "PlayNest",
    brandSlug: "playnest",
    ageGroup: "۳ تا ۵ سال",
    price: 2450000,
    oldPrice: 2890000,
    badge: "پرفروش",
    rating: 4.9,
    stock: 18,
    description:
      "یک ست ساختنی رنگارنگ برای تقویت خلاقیت، هماهنگی چشم و دست و بازی گروهی کودکان.",
    shortDescription: "ست ساختنی رنگارنگ برای بازی خلاقانه و امن.",
    imageClass: "from-amber-200 via-orange-100 to-rose-100",
  },
  {
    slug: "soft-cuddle-doll",
    name: "عروسک نرم کودک",
    category: "عروسک",
    categorySlug: "dolls",
    brand: "Mattel",
    brandSlug: "mattel",
    ageGroup: "۳ تا ۵ سال",
    price: 720000,
    badge: "جدید",
    rating: 4.8,
    stock: 22,
    description:
      "عروسکی سبک، نرم و دوست‌داشتنی برای بازی‌های خیالی و همراهی روزمره کودک.",
    shortDescription: "عروسک نرم و سبک برای بازی‌های خیالی.",
    imageClass: "from-rose-200 via-pink-100 to-purple-100",
  },
  {
    slug: "remote-control-racer",
    name: "ماشین مسابقه کنترلی",
    category: "ماشین اسباب‌بازی",
    categorySlug: "toy-cars",
    brand: "PlayNest",
    brandSlug: "playnest",
    ageGroup: "۹ تا ۱۲ سال",
    price: 2150000,
    oldPrice: 2390000,
    badge: "تخفیف",
    rating: 4.7,
    stock: 12,
    description:
      "ماشین کنترلی سریع و مقاوم برای مسابقه‌های هیجان‌انگیز در خانه و فضای باز.",
    shortDescription: "ماشین کنترلی مقاوم برای مسابقه و سرگرمی.",
    imageClass: "from-sky-200 via-cyan-100 to-blue-100",
  },
  {
    slug: "world-map-puzzle",
    name: "پازل نقشه جهان",
    category: "فکری و پازل",
    categorySlug: "puzzles",
    brand: "PlayNest",
    brandSlug: "playnest",
    ageGroup: "۶ تا ۸ سال",
    price: 650000,
    badge: "انتخاب خانواده",
    rating: 4.9,
    stock: 28,
    description:
      "پازلی آموزشی برای آشنایی کودکان با قاره‌ها، کشورها و مهارت حل مسئله.",
    shortDescription: "پازل آموزشی نقشه جهان برای یادگیری و تمرکز.",
    imageClass: "from-emerald-200 via-lime-100 to-yellow-100",
  },
  {
    slug: "learning-laptop",
    name: "لپ‌تاپ آموزشی کودک",
    category: "آموزشی",
    categorySlug: "educational",
    brand: "Fisher Price",
    brandSlug: "fisher-price",
    ageGroup: "۳ تا ۵ سال",
    price: 1680000,
    oldPrice: 1850000,
    badge: "محبوب",
    rating: 4.8,
    stock: 15,
    description:
      "اسباب‌بازی آموزشی با فعالیت‌های ساده برای شناخت حروف، اعداد و رنگ‌ها.",
    shortDescription: "لپ‌تاپ کودکانه برای یادگیری حروف و اعداد.",
    imageClass: "from-mint via-emerald-100 to-skysoft",
  },
  {
    slug: "baby-sensory-ball-set",
    name: "ست توپ حسی نوزاد",
    category: "نوزاد و خردسال",
    categorySlug: "baby-toddler",
    brand: "PlayNest",
    brandSlug: "playnest",
    ageGroup: "۰ تا ۲ سال",
    price: 490000,
    oldPrice: 560000,
    badge: "ایمن",
    rating: 4.9,
    stock: 40,
    description:
      "توپ‌های نرم با بافت‌های متنوع برای تقویت حس لمس و بازی ایمن نوزاد.",
    shortDescription: "توپ‌های حسی نرم و ایمن برای نوزادان.",
    imageClass: "from-orange-200 via-amber-100 to-cream",
  },
];

export const featuredProducts = products.slice(0, 4);

export const cartItems: CartItem[] = [
  { id: 1, product: products[0], quantity: 1 },
  { id: 2, product: products[3], quantity: 2 },
];

export const orders: Order[] = [
  {
    id: 1024,
    status: "pending",
    total: 2890000,
    date: "۱۴۰۳/۰۹/۱۲",
    itemCount: 2,
  },
  {
    id: 1018,
    status: "paid",
    total: 1680000,
    date: "۱۴۰۳/۰۸/۲۸",
    itemCount: 1,
  },
  {
    id: 1009,
    status: "shipped",
    total: 3500000,
    date: "۱۴۰۳/۰۸/۱۰",
    itemCount: 3,
  },
  {
    id: 1001,
    status: "delivered",
    total: 720000,
    date: "۱۴۰۳/۰۷/۲۴",
    itemCount: 1,
  },
];

export const benefits: Benefit[] = [
  {
    title: "اسباب‌بازی‌های ایمن",
    description: "محصولات منتخب با جنس مناسب کودک و راهنمای رده سنی.",
  },
  {
    title: "ارسال سریع",
    description: "ارسال مطمئن برای خانواده‌هایی که خرید آسان می‌خواهند.",
  },
  {
    title: "بازگشت آسان کالا",
    description: "فرآیند ساده مرجوعی برای تجربه خریدی بدون نگرانی.",
  },
  {
    title: "پرداخت امن",
    description: "مسیر پرداخت آماده و قابل اعتماد از ثبت سفارش تا تایید پرداخت.",
  },
];
