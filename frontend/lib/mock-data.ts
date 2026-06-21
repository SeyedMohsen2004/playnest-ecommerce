import {
  Blocks,
  Brain,
  Gamepad2,
  GraduationCap,
  Heart,
  Puzzle,
  UsersRound,
} from "lucide-react";

import type { Benefit, Brand, CartItem, Category, Order, Product } from "@/types";

export const categories: Category[] = [
  {
    slug: "board-games",
    title: "بردگیم",
    description: "بردگیم‌های خانوادگی، گروهی و استراتژیک برای دورهمی‌های جذاب.",
    href: "/products?category=board-games",
    icon: Gamepad2,
    color: "bg-sunshine/25 text-amber-700",
  },
  {
    slug: "mind-games",
    title: "بازی فکری",
    description: "بازی‌هایی برای تقویت تمرکز، حل مسئله و تصمیم‌گیری.",
    href: "/products?category=mind-games",
    icon: Brain,
    color: "bg-violet-100 text-violet-700",
  },
  {
    slug: "puzzles",
    title: "پازل",
    description: "پازل‌های تصویری و آموزشی برای کودک، نوجوان و بزرگسال.",
    href: "/products?category=puzzles",
    icon: Puzzle,
    color: "bg-skysoft text-sky-700",
  },
  {
    slug: "building-games",
    title: "لگو و ساختنی",
    description: "ست‌های ساختنی برای پرورش خلاقیت، دقت و بازی آزاد.",
    href: "/products?category=building-games",
    icon: Blocks,
    color: "bg-mint/25 text-emerald-700",
  },
  {
    slug: "educational-games",
    title: "بازی آموزشی",
    description: "محصولات آموزشی و سرگرم‌کننده برای یادگیری همراه با بازی.",
    href: "/products?category=educational-games",
    icon: GraduationCap,
    color: "bg-orange-100 text-orange-700",
  },
  {
    slug: "family-games",
    title: "بازی خانوادگی",
    description: "انتخاب‌هایی مناسب جمع خانواده و لحظه‌های مشترک و شاد.",
    href: "/products?category=family-games",
    icon: UsersRound,
    color: "bg-coral/20 text-rose-700",
  },
  {
    slug: "card-games",
    title: "بازی کارتی",
    description: "بازی‌های کارتی سریع، قابل حمل و مناسب دورهمی‌ها.",
    href: "/products?category=card-games",
    icon: Heart,
    color: "bg-cream text-coral",
  },
];

export const brands: Brand[] = [
  { slug: "ipaktoys", name: "IpakToys" },
  { slug: "lego", name: "LEGO" },
  { slug: "hasbro", name: "Hasbro" },
  { slug: "ravensburger", name: "Ravensburger" },
  { slug: "mindware", name: "MindWare" },
];

export const ageGroups = [
  "۳ تا ۵ سال",
  "۶ تا ۸ سال",
  "۹ تا ۱۲ سال",
  "۱۲ سال به بالا",
  "خانوادگی",
];

export const products: Product[] = [
  {
    slug: "lego-classic-box",
    name: "ست لگو کلاسیک خلاقانه",
    category: "لگو و ساختنی",
    categorySlug: "building-games",
    brand: "LEGO",
    brandSlug: "lego",
    ageGroup: "۶ تا ۸ سال",
    price: 2450000,
    oldPrice: 2890000,
    badge: "پرفروش",
    rating: 4.9,
    stock: 18,
    description:
      "یک ست ساختنی رنگارنگ برای تقویت خلاقیت، هماهنگی چشم و دست و ساخت ایده‌های تازه در خانه.",
    shortDescription: "ست ساختنی رنگارنگ برای بازی خلاقانه و مهارت‌آموزی.",
    imageClass: "from-amber-200 via-orange-100 to-rose-100",
  },
  {
    slug: "strategy-family-board-game",
    name: "بردگیم استراتژی خانوادگی",
    category: "بردگیم",
    categorySlug: "board-games",
    brand: "IpakToys",
    brandSlug: "ipaktoys",
    ageGroup: "۱۲ سال به بالا",
    price: 1680000,
    oldPrice: 1890000,
    badge: "پیشنهاد ویژه",
    rating: 4.8,
    stock: 16,
    description:
      "یک بازی رومیزی جذاب برای جمع‌های خانوادگی که برنامه‌ریزی، تعامل و تصمیم‌گیری را به چالش می‌کشد.",
    shortDescription: "بردگیم خانوادگی مناسب دورهمی و رقابت دوستانه.",
    imageClass: "from-coral/30 via-orange-100 to-sunshine/40",
  },
  {
    slug: "persian-word-card-game",
    name: "بازی کارتی کلمات فارسی",
    category: "بازی کارتی",
    categorySlug: "card-games",
    brand: "IpakToys",
    brandSlug: "ipaktoys",
    ageGroup: "۹ تا ۱۲ سال",
    price: 520000,
    badge: "جدید",
    rating: 4.7,
    stock: 28,
    description:
      "بازی کارتی سریع و آموزشی برای تقویت دایره واژگان، سرعت عمل و تعامل گروهی.",
    shortDescription: "بازی کارتی جمع‌وجور برای خانواده و مهمانی.",
    imageClass: "from-sky-200 via-cyan-100 to-blue-100",
  },
  {
    slug: "world-map-puzzle",
    name: "پازل نقشه جهان",
    category: "پازل",
    categorySlug: "puzzles",
    brand: "Ravensburger",
    brandSlug: "ravensburger",
    ageGroup: "۶ تا ۸ سال",
    price: 650000,
    badge: "انتخاب خانواده",
    rating: 4.9,
    stock: 28,
    description:
      "پازلی آموزشی برای آشنایی با قاره‌ها، کشورها و تقویت تمرکز و حل مسئله.",
    shortDescription: "پازل آموزشی نقشه جهان برای یادگیری و تمرکز.",
    imageClass: "from-emerald-200 via-lime-100 to-yellow-100",
  },
  {
    slug: "junior-mind-challenge",
    name: "چالش فکری کودک",
    category: "بازی فکری",
    categorySlug: "mind-games",
    brand: "MindWare",
    brandSlug: "mindware",
    ageGroup: "۶ تا ۸ سال",
    price: 940000,
    oldPrice: 1080000,
    badge: "محبوب",
    rating: 4.8,
    stock: 21,
    description:
      "مجموعه‌ای از کارت‌ها و معماهای مرحله‌ای برای تمرین تمرکز، حافظه و حل مسئله.",
    shortDescription: "بازی فکری مرحله‌ای برای تقویت مهارت‌های ذهنی.",
    imageClass: "from-mint via-emerald-100 to-skysoft",
  },
  {
    slug: "family-deduction-game",
    name: "بازی گروهی معمایی خانواده",
    category: "بازی خانوادگی",
    categorySlug: "family-games",
    brand: "Hasbro",
    brandSlug: "hasbro",
    ageGroup: "خانوادگی",
    price: 1320000,
    oldPrice: 1490000,
    badge: "دورهمی",
    rating: 4.9,
    stock: 12,
    description:
      "یک بازی گروهی با نقش‌آفرینی سبک و معماهای کوتاه برای شب‌های دورهمی خانوادگی.",
    shortDescription: "بازی خانوادگی مناسب تعامل، گفت‌وگو و هیجان جمعی.",
    imageClass: "from-purple-200 via-pink-100 to-cream",
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
    title: "انتخاب مناسب سن و جمع",
    description: "محصولات با توضیح رده سنی، تعداد بازیکن و سبک بازی معرفی می‌شوند.",
  },
  {
    title: "ارسال سریع",
    description: "ارسال مطمئن برای خانواده‌ها و علاقه‌مندان بازی‌های رومیزی.",
  },
  {
    title: "بازگشت آسان کالا",
    description: "فرآیند ساده مرجوعی بر اساس شرایط کالا و بسته‌بندی.",
  },
  {
    title: "پرداخت امن",
    description: "مسیر پرداخت آماده و قابل اعتماد از ثبت سفارش تا تایید پرداخت.",
  },
];
