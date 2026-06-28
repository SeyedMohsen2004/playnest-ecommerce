import Link from "next/link";

import type { Category } from "@/types";

export function CategoryCard({ category }: { category: Category }) {
  const Icon = category.icon;

  return (
    <Link
      href={category.href}
      className="group relative overflow-hidden rounded-[1.5rem] border border-white/70 bg-white/82 p-4 shadow-card backdrop-blur transition duration-300 hover:-translate-y-1 hover:shadow-soft"
    >
      <span className="pointer-events-none absolute -left-7 -top-7 size-20 rounded-full bg-coral/10 transition group-hover:scale-125" />
      <span
        className={`relative flex size-11 items-center justify-center rounded-[1.1rem] shadow-sm ${category.color}`}
      >
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <h3 className="relative mt-3 text-base font-black text-ink">
        {category.title}
      </h3>
      <p className="relative mt-1.5 line-clamp-2 text-xs leading-6 text-ink/60">
        {category.description}
      </p>
      <p className="mt-3 text-xs font-bold text-coral transition group-hover:-translate-x-1">
        مشاهده دسته‌بندی
      </p>
    </Link>
  );
}
