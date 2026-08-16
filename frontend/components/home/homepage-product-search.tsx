"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";

export function HomepageProductSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const trimmedQuery = query.trim();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!trimmedQuery) {
      return;
    }

    const searchParams = new URLSearchParams({ search: trimmedQuery });
    router.push(`/products?${searchParams.toString()}`);
  }

  return (
    <section
      aria-labelledby="homepage-product-search-title"
      className="mx-auto max-w-7xl px-4 pb-6 sm:px-6 sm:pb-8 lg:px-8"
    >
      <div className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-white/78 p-5 shadow-soft backdrop-blur dark:border-white/10 sm:p-7 lg:grid lg:grid-cols-[0.72fr_1.28fr] lg:items-center lg:gap-8">
        <div className="pointer-events-none absolute -left-12 -top-16 size-40 rounded-full bg-mint/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 right-10 size-44 rounded-full bg-coral/15 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-black text-coral sm:text-sm">
            سریع‌تر پیداش کن
          </p>
          <h2
            className="mt-1 text-xl font-black tracking-tight text-ink sm:text-2xl"
            id="homepage-product-search-title"
          >
            جستجوی محصولات
          </h2>
          <p className="mt-2 text-sm leading-7 text-ink/60">
            نام بازی، اسباب‌بازی یا محصول مورد نظرتان را بنویسید.
          </p>
        </div>

        <form
          className="relative mt-5 flex flex-col gap-3 sm:flex-row lg:mt-0"
          onSubmit={handleSubmit}
          role="search"
        >
          <label className="sr-only" htmlFor="homepage-product-search">
            جستجوی محصولات
          </label>
          <div className="relative flex-1">
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute right-4 top-1/2 size-5 -translate-y-1/2 text-coral"
            />
            <input
              autoComplete="off"
              className="h-14 w-full rounded-2xl border border-ink/10 bg-cream/60 pl-4 pr-12 text-sm text-ink outline-none transition placeholder:text-ink/40 focus:border-coral focus:bg-white focus:ring-2 focus:ring-coral/15 dark:focus:bg-white/10 sm:text-base"
              dir="auto"
              enterKeyHint="search"
              id="homepage-product-search"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="نام بازی یا محصول را جستجو کنید"
              type="search"
              value={query}
            />
          </div>
          <Button
            className="h-14 px-8 sm:shrink-0"
            disabled={!trimmedQuery}
            size="lg"
            type="submit"
            variant="coral"
          >
            <Search aria-hidden="true" className="size-5" />
            جستجو
          </Button>
        </form>
      </div>
    </section>
  );
}
