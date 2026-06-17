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
    title: "لگو و ساختنی",
    description: "لگو، آجرهای رنگی، کاشی مغناطیسی و بازی‌های ساختنی.",
    href: "#categories",
    icon: Blocks,
    color: "bg-sunshine/25 text-amber-700",
  },
  {
    title: "عروسک",
    description: "عروسک‌های نرم، فانتزی و دوست‌داشتنی برای بازی‌های خیالی.",
    href: "#categories",
    icon: Heart,
    color: "bg-coral/20 text-rose-700",
  },
  {
    title: "ماشین اسباب‌بازی",
    description: "ماشین فلزی، پیست مسابقه و خودروهای کنترلی هیجان‌انگیز.",
    href: "#categories",
    icon: Car,
    color: "bg-skysoft text-sky-700",
  },
  {
    title: "آموزشی",
    description: "کارت آموزشی، بازی علمی و ابزارهای یادگیری کودکانه.",
    href: "#categories",
    icon: GraduationCap,
    color: "bg-mint/25 text-emerald-700",
  },
  {
    title: "فکری و پازل",
    description: "پازل، بازی فکری و سرگرمی‌های خانوادگی برای ذهن‌های کنجکاو.",
    href: "#categories",
    icon: Puzzle,
    color: "bg-violet-100 text-violet-700",
  },
  {
    title: "نوزاد و خردسال",
    description: "اسباب‌بازی‌های ایمن و حسی برای دست‌های کوچک و کنجکاو.",
    href: "#categories",
    icon: Brain,
    color: "bg-orange-100 text-orange-700",
  },
];

export const featuredProducts: Product[] = [
  {
    name: "بلوک‌های ساختنی رنگین‌کمان",
    category: "لگو و ساختنی",
    price: 2450000,
    oldPrice: 2890000,
    badge: "پرفروش",
    rating: 4.9,
    imageClass: "from-amber-200 via-orange-100 to-rose-100",
  },
  {
    name: "عروسک نرم کودک",
    category: "عروسک",
    price: 720000,
    badge: "جدید",
    rating: 4.8,
    imageClass: "from-rose-200 via-pink-100 to-purple-100",
  },
  {
    name: "ماشین مسابقه کنترلی",
    category: "ماشین اسباب‌بازی",
    price: 2150000,
    oldPrice: 2390000,
    badge: "تخفیف",
    rating: 4.7,
    imageClass: "from-sky-200 via-cyan-100 to-blue-100",
  },
  {
    name: "پازل نقشه جهان",
    category: "فکری و پازل",
    price: 650000,
    badge: "انتخاب خانواده",
    rating: 4.9,
    imageClass: "from-emerald-200 via-lime-100 to-yellow-100",
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
