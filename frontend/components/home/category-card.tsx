import Link from "next/link";

import type { Category } from "@/types";

export function CategoryCard({ category }: { category: Category }) {
  const Icon = category.icon;

  return (
    <Link
      href={category.href}
      className="group rounded-3xl border border-ink/5 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-soft"
    >
      <span
        className={`flex size-14 items-center justify-center rounded-2xl ${category.color}`}
      >
        <Icon className="size-7" aria-hidden="true" />
      </span>
      <h3 className="mt-5 text-lg font-black text-ink">{category.title}</h3>
      <p className="mt-2 text-sm leading-6 text-ink/60">{category.description}</p>
      <p className="mt-4 text-sm font-bold text-coral transition group-hover:translate-x-1">
        Shop category
      </p>
    </Link>
  );
}
