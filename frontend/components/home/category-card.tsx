import Link from "next/link";

import type { Category } from "@/types";

export function CategoryCard({ category }: { category: Category }) {
  const Icon = category.icon;

  return (
    <Link
      href={category.href}
      className="group relative overflow-hidden rounded-[2rem] border border-white/70 bg-white/82 p-5 shadow-card backdrop-blur transition duration-300 hover:-translate-y-2 hover:shadow-soft"
    >
      <span className="pointer-events-none absolute -left-8 -top-8 size-24 rounded-full bg-coral/10 transition group-hover:scale-125" />
      <span
        className={`relative flex size-14 items-center justify-center rounded-2xl shadow-sm ${category.color}`}
      >
        <Icon className="size-7" aria-hidden="true" />
      </span>
      <h3 className="relative mt-5 text-lg font-black text-ink">
        {category.title}
      </h3>
      <p className="relative mt-2 text-sm leading-7 text-ink/60">
        {category.description}
      </p>
      <p className="mt-4 text-sm font-bold text-coral transition group-hover:-translate-x-1">
        مشاهده دسته‌بندی
      </p>
    </Link>
  );
}
