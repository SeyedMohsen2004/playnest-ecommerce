"use client";

import { ClipboardList, LogOut, Menu, ShoppingCart, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
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
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const displayName =
    user?.first_name?.trim() || user?.phone_number || "حساب کاربری";

  function handleLogout() {
    logout();
    setIsOpen(false);
    router.push("/");
  }

  function isActiveLink(href: string) {
    if (href.includes("#")) {
      return false;
    }

    const path = href.split("#")[0];

    if (path === "/") {
      return pathname === "/";
    }

    return pathname === path || pathname.startsWith(`${path}/`);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-white/60 bg-cream/78 shadow-[0_10px_40px_rgba(23,32,51,0.06)] backdrop-blur-xl dark:border-white/10 dark:bg-[rgb(var(--surface)/0.88)]">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="relative block size-11 shrink-0 overflow-hidden rounded-[1.05rem] shadow-[0_10px_24px_rgba(23,32,51,0.10)] sm:size-12">
            <Image
              alt="لوگوی ایپک تویز"
              className="h-full w-full object-contain"
              height={48}
              priority
              src="/images/brand/ipacktoys-logo.png"
              width={48}
            />
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-2xl font-black tracking-tight text-ink">
              IpakToys
            </span>
            <span className="mt-1 text-[0.65rem] font-bold text-coral">
              ایپک تویز | بازی فکری، بردگیم و پازل
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-2 rounded-full bg-white/55 p-1 shadow-sm ring-1 ring-white/70 dark:bg-white/10 dark:ring-white/10 lg:flex">
          {navigation.map((item) => {
            const isActive = isActiveLink(item.href);

            return (
              <Link
                href={item.href}
                key={item.label}
                className={cn(
                  "rounded-full px-4 py-2 text-sm font-bold text-ink/70 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-coral/70 hover:bg-white hover:text-coral hover:shadow-sm dark:text-ink/90 dark:hover:bg-white/10 dark:hover:text-sunshine",
                  isActive
                    ? "bg-white text-coral shadow-sm dark:bg-white/15 dark:text-sunshine"
                    : "",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <ThemeToggle />
          <Button
            asChild
            variant="ghost"
            size="sm"
            aria-label="باز کردن سبد خرید"
            className="bg-white/65 shadow-sm"
          >
            <Link href="/cart">
              <ShoppingCart className="size-5" />
              سبد خرید
            </Link>
          </Button>

          {isAuthenticated ? (
            <>
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="bg-white/65 shadow-sm"
              >
                <Link href="/account/orders">
                  <ClipboardList className="size-5" />
                  سفارش‌های من
                </Link>
              </Button>
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
          className="flex size-11 items-center justify-center rounded-2xl bg-white text-ink shadow-sm ring-1 ring-white/70 transition hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine lg:hidden"
          aria-label="باز و بسته کردن منو"
          onClick={() => setIsOpen((current) => !current)}
        >
          {isOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      <div
        className={cn(
          "grid border-t border-ink/5 bg-white/95 transition-all dark:border-white/10 dark:bg-[rgb(var(--surface)/0.98)] lg:hidden",
          isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <div className="overflow-hidden">
          <nav className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-4 sm:px-6">
            {navigation.map((item) => {
              const isActive = isActiveLink(item.href);

              return (
                <Link
                  href={item.href}
                  key={item.label}
                  className={cn(
                    "rounded-2xl px-4 py-3 text-sm font-bold text-ink/80 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-coral/70 hover:bg-cream hover:text-ink dark:text-ink/90 dark:hover:bg-white/10 dark:hover:text-sunshine",
                    isActive
                      ? "bg-cream text-coral dark:bg-white/15 dark:text-sunshine"
                      : "",
                  )}
                  onClick={() => setIsOpen(false)}
                >
                  {item.label}
                </Link>
              );
            })}

            {isAuthenticated ? (
              <div className="grid gap-3 pt-3">
                <ThemeToggle />
                <div className="rounded-2xl bg-cream px-4 py-3 text-sm font-black text-ink">
                  {displayName}
                </div>
                <Button asChild variant="outline">
                  <Link
                    href="/account/orders"
                    onClick={() => setIsOpen(false)}
                  >
                    <ClipboardList className="size-5" />
                    سفارش‌های من
                  </Link>
                </Button>
                <Button onClick={handleLogout} variant="outline">
                  <LogOut className="size-5" />
                  خروج
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 pt-3">
                <div className="col-span-2">
                  <ThemeToggle />
                </div>
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

            <Button
              asChild
              className="mt-3 h-12 justify-center rounded-2xl bg-gradient-to-l from-coral via-candy to-grape px-5 text-sm font-black text-white shadow-glow ring-1 ring-white/20 transition hover:-translate-y-0.5 hover:from-candy hover:to-coral hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sunshine/80 active:translate-y-0 dark:text-white dark:shadow-[0_18px_45px_rgba(255,91,155,0.22)]"
              variant="default"
            >
              <Link href="/cart" onClick={() => setIsOpen(false)}>
                <ShoppingCart className="size-5 shrink-0" />
                مشاهده سبد خرید
              </Link>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
