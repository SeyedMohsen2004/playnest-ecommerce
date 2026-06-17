"use client";

import { Menu, ShoppingCart, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { label: "Toys", href: "#products" },
  { label: "Categories", href: "#categories" },
  { label: "Offers", href: "#offers" },
  { label: "Why PlayNest", href: "#benefits" },
];

export function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-ink/5 bg-cream/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex size-11 items-center justify-center rounded-2xl bg-coral text-white shadow-soft">
            <Sparkles className="size-5" aria-hidden="true" />
          </span>
          <span className="text-2xl font-black tracking-tight text-ink">
            PlayNest
          </span>
        </Link>

        <nav className="hidden items-center gap-8 lg:flex">
          {navigation.map((item) => (
            <Link
              href={item.href}
              key={item.label}
              className="text-sm font-semibold text-ink/70 transition hover:text-ink"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Button variant="ghost" size="sm" aria-label="Open cart">
            <ShoppingCart className="size-5" />
            Cart
          </Button>
          <Button variant="outline" size="sm">
            Login
          </Button>
          <Button variant="coral" size="sm">
            Register
          </Button>
        </div>

        <button
          type="button"
          className="flex size-11 items-center justify-center rounded-2xl bg-white text-ink shadow-sm lg:hidden"
          aria-label="Toggle navigation"
          onClick={() => setIsOpen((current) => !current)}
        >
          {isOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      <div
        className={cn(
          "grid border-t border-ink/5 bg-white/95 transition-all lg:hidden",
          isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <div className="overflow-hidden">
          <nav className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-4 sm:px-6">
            {navigation.map((item) => (
              <Link
                href={item.href}
                key={item.label}
                className="rounded-2xl px-4 py-3 text-sm font-semibold text-ink/75 transition hover:bg-cream hover:text-ink"
                onClick={() => setIsOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <div className="grid grid-cols-2 gap-3 pt-3">
              <Button variant="outline">Login</Button>
              <Button variant="coral">Register</Button>
            </div>
            <Button className="mt-2" variant="default">
              <ShoppingCart className="size-5" />
              View cart
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
