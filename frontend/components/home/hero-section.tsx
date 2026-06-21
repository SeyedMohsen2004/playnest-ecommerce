import { ArrowLeft, Gift, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-1/2 top-10 -z-10 size-[26rem] -translate-x-1/2 rounded-full bg-coral/10 blur-3xl sm:size-[36rem]" />
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-24">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-bold text-coral shadow-sm">
            <Sparkles className="size-4" />
            انتخاب‌های تازه برای دورهمی و خلاقیت
          </div>
          <h1 className="mt-6 max-w-3xl text-5xl font-black tracking-tight text-ink sm:text-6xl lg:text-7xl">
            دنیای بازی‌های فکری، بردگیم و سرگرمی‌های ساختنی
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/65">
            در IpakToys بازی‌های فکری، بردگیم‌ها، پازل‌ها و محصولات ساختنی
            مناسب کودک، نوجوان و خانواده را با تجربه خریدی ساده و مطمئن پیدا
            کنید.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" variant="coral">
              <Link href="/products">
                مشاهده محصولات <ArrowLeft className="size-5" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="#offers">پیشنهادهای ویژه</Link>
            </Button>
          </div>
          <div className="mt-8 grid gap-4 text-sm font-semibold text-ink/70 sm:grid-cols-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-5 text-emerald-500" />
              انتخاب مناسب سن و سبک بازی
            </div>
            <div className="flex items-center gap-2">
              <Gift className="size-5 text-coral" />
              گزینه‌های مناسب هدیه و دورهمی
            </div>
          </div>
        </div>

        <div className="relative z-0">
          <div className="rounded-[2.5rem] bg-white p-5 shadow-soft">
            <div className="relative min-h-[26rem] overflow-hidden rounded-[2rem] bg-gradient-to-br from-skysoft via-cream to-coral/20 p-6">
              <div className="relative z-10 w-fit rounded-3xl bg-white/80 px-4 py-3 text-sm font-bold text-ink shadow-sm">
                امتیاز ۴.۹ از خریداران
              </div>
              <div className="absolute bottom-8 left-6 right-6 z-10 rounded-3xl bg-white/90 p-5 shadow-soft backdrop-blur sm:left-8 sm:right-8">
                <p className="text-sm font-bold uppercase tracking-wide text-coral">
                  بسته پیشنهادی
                </p>
                <h2 className="mt-2 text-2xl font-black text-ink">
                  بردگیم و پازل برای شب خانواده
                </h2>
                <p className="mt-2 text-sm leading-6 text-ink/60">
                  ترکیبی از بازی رومیزی، پازل و محصولات ساختنی برای سرگرمی،
                  یادگیری و رقابت دوستانه.
                </p>
              </div>
              <div className="pointer-events-none absolute left-8 top-24 z-0 hidden size-24 rotate-12 rounded-3xl bg-sunshine/80 shadow-soft sm:block lg:left-10 lg:top-20 lg:size-28" />
              <div className="pointer-events-none absolute right-12 top-32 z-0 hidden size-20 -rotate-12 rounded-full bg-mint/80 shadow-soft sm:block lg:right-20 lg:size-24" />
              <div className="pointer-events-none absolute bottom-36 left-24 z-0 hidden size-16 rounded-2xl bg-coral/80 shadow-soft sm:block lg:left-28 lg:size-20" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
