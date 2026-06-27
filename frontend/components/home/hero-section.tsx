import { ArrowLeft, Gift, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-full bg-[radial-gradient(circle_at_78%_12%,rgba(255,209,102,0.34),transparent_18rem),radial-gradient(circle_at_12%_18%,rgba(150,216,206,0.34),transparent_20rem)]" />
      <div className="pointer-events-none absolute left-1/2 top-10 -z-10 size-[24rem] -translate-x-1/2 rounded-full bg-coral/10 blur-3xl sm:size-[36rem]" />

      <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 sm:py-18 lg:grid-cols-2 lg:px-8 lg:py-24">
        <div className="relative z-10">
          <div className="inline-flex max-w-full items-center gap-2 rounded-full bg-white/90 px-4 py-2 text-sm font-bold leading-7 text-coral shadow-sm">
            <Sparkles className="size-4 shrink-0" />
            <span>انتخاب‌های تازه برای دورهمی، خلاقیت و یادگیری</span>
          </div>

          <h1 className="mt-7 max-w-3xl text-4xl font-black leading-[1.35] tracking-tight text-ink sm:text-5xl sm:leading-[1.28] lg:text-6xl lg:leading-[1.22]">
            دنیای بازی‌های فکری، بردگیم و سرگرمی‌های ساختنی
          </h1>

          <p className="mt-6 max-w-2xl text-base leading-9 text-ink/68 sm:text-lg sm:leading-10">
            در IpakToys بازی‌های فکری، بردگیم‌ها، پازل‌ها و محصولات ساختنی
            مناسب کودک، نوجوان و خانواده را با تجربه خریدی ساده و مطمئن پیدا
            کنید.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button asChild className="h-12 px-7" size="lg" variant="coral">
              <Link href="/products">
                مشاهده محصولات <ArrowLeft className="size-5" />
              </Link>
            </Button>
            <Button asChild className="h-12 px-7" size="lg" variant="outline">
              <Link href="#offers">پیشنهادهای ویژه</Link>
            </Button>
          </div>

          <div className="mt-9 grid gap-3 text-sm font-semibold leading-7 text-ink/70 sm:grid-cols-2">
            <div className="flex items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 shadow-sm">
              <ShieldCheck className="size-5 shrink-0 text-emerald-500" />
              انتخاب مناسب سن و سبک بازی
            </div>
            <div className="flex items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 shadow-sm">
              <Gift className="size-5 shrink-0 text-coral" />
              گزینه‌های مناسب هدیه و دورهمی
            </div>
          </div>
        </div>

        <div className="relative z-0">
          <div className="absolute -right-4 top-8 hidden size-16 rotate-12 rounded-[1.5rem] bg-sunshine/70 shadow-soft sm:block" />
          <div className="absolute -left-2 top-24 hidden size-12 rounded-full bg-mint/70 shadow-soft sm:block" />
          <div className="rounded-[2.75rem] bg-white/90 p-4 shadow-soft ring-1 ring-ink/5 sm:p-5">
            <div className="relative min-h-[24rem] overflow-hidden rounded-[2.25rem] bg-gradient-to-br from-skysoft via-cream to-coral/20 p-6 sm:min-h-[27rem] sm:p-7">
              <div className="relative z-10 w-fit rounded-3xl bg-white/85 px-4 py-3 text-sm font-bold leading-7 text-ink shadow-sm">
                بردگیم، پازل و بازی فکری برای خانواده
              </div>

              <div className="absolute left-7 top-24 z-0 size-24 rotate-12 rounded-[2rem] bg-sunshine/80 shadow-soft sm:size-28" />
              <div className="absolute right-10 top-32 z-0 size-20 -rotate-12 rounded-full bg-mint/80 shadow-soft sm:right-16 sm:size-24" />
              <div className="absolute bottom-36 left-20 z-0 size-16 rounded-2xl bg-coral/75 shadow-soft sm:left-24 sm:size-20" />
              <div className="absolute right-8 top-10 z-0 grid grid-cols-2 gap-2 rounded-3xl bg-white/55 p-3 shadow-sm">
                {Array.from({ length: 4 }).map((_, index) => (
                  <span
                    className="size-3 rounded-full bg-coral/55"
                    key={index}
                  />
                ))}
              </div>

              <div className="absolute bottom-7 left-5 right-5 z-10 rounded-3xl bg-white/92 p-5 shadow-soft backdrop-blur sm:left-8 sm:right-8 sm:p-6">
                <p className="text-sm font-bold uppercase tracking-wide text-coral">
                  پیشنهاد IpakToys
                </p>
                <h2 className="mt-3 text-2xl font-black leading-9 text-ink">
                  بازی مناسب شب خانواده و جمع دوستان
                </h2>
                <p className="mt-3 text-sm leading-8 text-ink/62">
                  ترکیبی از بازی رومیزی، پازل و محصولات ساختنی برای سرگرمی،
                  یادگیری و رقابت دوستانه.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
