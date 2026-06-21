"use client";

import { LogOut, Menu, ShoppingCart, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { label: "خانه", href: "/" },
  { label: "محصولات", href: "/products" },
  { label: "دسته‌بندی‌ها", href: "/products#filters" },
  { label: "پیشنهادها", href: "/#offers" },
];

export function SiteHeader() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const displayName =
    user?.first_name?.trim() || user?.phone_number || "حساب کاربری";

  function handleLogout() {
    logout();
    setIsOpen(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-ink/5 bg-cream/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex size-11 items-center justify-center rounded-2xl bg-coral text-white shadow-soft">
            <Sparkles className="size-5" aria-hidden="true" />
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-2xl font-black tracking-tight text-ink">
              IpakToys
            </span>
            <span className="mt-1 text-[0.65rem] font-bold text-coral">
              بازی فکری، بردگیم و پازل
            </span>
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
          <Button
            asChild
            variant="ghost"
            size="sm"
            aria-label="باز کردن سبد خرید"
          >
            <Link href="/cart">
              <ShoppingCart className="size-5" />
              سبد خرید
            </Link>
          </Button>

          {isAuthenticated ? (
            <>
              <span className="max-w-32 truncate rounded-full bg-white px-4 py-2 text-xs font-black text-ink shadow-sm">
                {displayName}
              </span>
              <Button onClick={handleLogout} variant="outline" size="sm">
                <LogOut className="size-4" />
                خروج
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="outline" size="sm">
                <Link href="/login">ورود</Link>
              </Button>
              <Button asChild variant="coral" size="sm">
                <Link href="/register">ثبت‌نام</Link>
              </Button>
            </>
          )}

          {isLoading && !isAuthenticated ? (
            <span className="text-xs font-bold text-ink/40">
              در حال بررسی...
            </span>
          ) : null}
        </div>

        <button
          type="button"
          className="flex size-11 items-center justify-center rounded-2xl bg-white text-ink shadow-sm lg:hidden"
          aria-label="باز و بسته کردن منو"
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

            {isAuthenticated ? (
              <div className="grid gap-3 pt-3">
                <div className="rounded-2xl bg-cream px-4 py-3 text-sm font-black text-ink">
                  {displayName}
                </div>
                <Button onClick={handleLogout} variant="outline">
                  <LogOut className="size-5" />
                  خروج
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 pt-3">
                <Button asChild variant="outline">
                  <Link href="/login" onClick={() => setIsOpen(false)}>
                    ورود
                  </Link>
                </Button>
                <Button asChild variant="coral">
                  <Link href="/register" onClick={() => setIsOpen(false)}>
                    ثبت‌نام
                  </Link>
                </Button>
              </div>
            )}

            <Button asChild className="mt-2" variant="default">
              <Link href="/cart" onClick={() => setIsOpen(false)}>
                <ShoppingCart className="size-5" />
                مشاهده سبد خرید
              </Link>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
