"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";

export function ProductSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const trimmedQuery = query.trim();

  function submitSearch() {
    if (!trimmedQuery) {
      return;
    }

    const searchParams = new URLSearchParams({ search: trimmedQuery });
    router.push(`/products?${searchParams.toString()}`);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitSearch();
  }

  return (
    <form
      className="flex w-full items-center gap-2 xl:max-w-md"
      onSubmit={handleSubmit}
      role="search"
    >
      <label className="sr-only" htmlFor="site-product-search">
        جستجوی محصولات
      </label>
      <div className="relative min-w-0 flex-1">
        <Search
          aria-hidden="true"
          className="pointer-events-none absolute right-4 top-1/2 size-4 -translate-y-1/2 text-coral"
        />
        <input
          autoComplete="off"
          className="h-11 w-full rounded-2xl border border-ink/10 bg-white/70 pl-3 pr-10 text-sm text-ink outline-none transition placeholder:text-ink/40 focus:border-coral focus:bg-white focus:ring-2 focus:ring-coral/15 dark:bg-white/10 dark:focus:bg-white/15"
          dir="auto"
          enterKeyHint="search"
          id="site-product-search"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              submitSearch();
            }
          }}
          placeholder="نام بازی یا محصول را جستجو کنید"
          type="search"
          value={query}
        />
      </div>
      <Button
        className="h-11 shrink-0 px-4"
        disabled={!trimmedQuery}
        size="sm"
        type="submit"
        variant="coral"
      >
        <Search aria-hidden="true" className="size-4" />
        جستجو
      </Button>
    </form>
  );
}
