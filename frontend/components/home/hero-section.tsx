import { ArrowLeft, Gift, Puzzle, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const playStyles = ["بردگیم", "پازل", "بازی فکری", "ساختنی"];

export function HeroSection() {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_82%_10%,rgba(255,209,102,0.38),transparent_18rem),radial-gradient(circle_at_8%_18%,rgba(110,231,183,0.24),transparent_22rem),linear-gradient(180deg,rgba(255,248,237,0.98),rgba(255,255,255,0.72))]" />
      <div className="pointer-events-none absolute right-4 top-16 -z-10 size-24 rounded-[2rem] bg-coral/10 blur-2xl sm:right-12 sm:size-40" />
      <div className="pointer-events-none absolute bottom-14 left-5 -z-10 size-28 rounded-full bg-skysoft/80 blur-2xl sm:left-16 sm:size-48" />

      <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 sm:py-16 lg:grid-cols-[1.02fr_0.98fr] lg:px-8 lg:py-24">
        <div className="relative z-10">
          <div className="inline-flex max-w-full items-center gap-2 rounded-full border border-coral/10 bg-white/90 px-4 py-2 text-sm font-bold leading-7 text-coral shadow-sm">
            <Sparkles className="size-4 shrink-0" />
            <span>انتخاب‌های تازه برای بازی، خلاقیت و دورهمی</span>
          </div>

          <h1 className="mt-7 max-w-3xl text-4xl font-black leading-[1.36] tracking-tight text-ink sm:text-5xl sm:leading-[1.3] lg:text-6xl lg:leading-[1.24]">
            دنیای رنگی بازی‌های فکری، بردگیم و سرگرمی‌های ساختنی
          </h1>

          <p className="mt-6 max-w-2xl text-base leading-9 text-ink/68 sm:text-lg sm:leading-10">
            در IpakToys بازی‌های فکری، بردگیم‌ها، پازل‌ها و محصولات ساختنی
            مناسب کودک، نوجوان و خانواده را با تجربه خریدی ساده و مطمئن پیدا
            کنید.
          </p>

          <div className="mt-8 flex flex-wrap gap-2">
            {playStyles.map((item) => (
              <span
                className="rounded-full bg-white/80 px-4 py-2 text-xs font-black text-ink/60 shadow-sm ring-1 ring-ink/5"
                key={item}
              >
                {item}
              </span>
            ))}
          </div>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button
              asChild
              className="h-12 rounded-2xl px-7 shadow-[0_14px_32px_rgba(255,122,122,0.26)]"
              size="lg"
              variant="coral"
            >
              <Link href="/products">
                مشاهده محصولات <ArrowLeft className="size-5" />
              </Link>
            </Button>
            <Button
              asChild
              className="h-12 rounded-2xl border-white bg-white/86 px-7"
              size="lg"
              variant="outline"
            >
              <Link href="#offers">پیشنهادهای ویژه</Link>
            </Button>
          </div>

          <div className="mt-9 grid gap-3 text-sm font-semibold leading-7 text-ink/70 sm:grid-cols-2">
            <div className="flex items-center gap-2 rounded-2xl bg-white/75 px-4 py-3 shadow-sm ring-1 ring-ink/5">
              <ShieldCheck className="size-5 shrink-0 text-emerald-500" />
              انتخاب مناسب سن و سبک بازی
            </div>
            <div className="flex items-center gap-2 rounded-2xl bg-white/75 px-4 py-3 shadow-sm ring-1 ring-ink/5">
              <Gift className="size-5 shrink-0 text-coral" />
              گزینه‌های مناسب هدیه و دورهمی
            </div>
          </div>
        </div>

        <div className="relative z-0">
          <div className="pointer-events-none absolute -right-3 top-7 hidden size-16 rotate-12 rounded-[1.5rem] bg-sunshine/70 shadow-soft sm:block" />
          <div className="pointer-events-none absolute -left-4 top-28 hidden size-12 rounded-full bg-mint/70 shadow-soft sm:block" />
          <div className="pointer-events-none absolute bottom-10 right-10 hidden size-8 rounded-full bg-coral/45 sm:block" />

          <div className="rounded-[2.75rem] bg-white/80 p-3 shadow-soft ring-1 ring-white/80 backdrop-blur sm:p-5">
            <div className="relative min-h-[24rem] overflow-hidden rounded-[2.35rem] bg-gradient-to-br from-skysoft via-cream to-coral/20 p-6 sm:min-h-[27rem] sm:p-7">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.86),transparent_7rem),radial-gradient(circle_at_82%_28%,rgba(255,209,102,0.34),transparent_7rem)]" />

              <div className="relative z-10 flex w-fit items-center gap-2 rounded-3xl bg-white/88 px-4 py-3 text-sm font-bold leading-7 text-ink shadow-sm">
                <Puzzle className="size-5 text-coral" />
                بردگیم، پازل و بازی فکری برای خانواده
              </div>

              <div className="absolute left-8 top-24 z-0 size-24 rotate-12 rounded-[2rem] bg-sunshine/80 shadow-soft sm:size-28" />
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

              <div className="absolute bottom-7 left-5 right-5 z-10 rounded-[2rem] bg-white/94 p-5 shadow-soft backdrop-blur sm:left-8 sm:right-8 sm:p-6">
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
