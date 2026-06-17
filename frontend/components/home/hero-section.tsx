import { ArrowLeft, Gift, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute left-1/2 top-10 -z-10 size-[36rem] -translate-x-1/2 rounded-full bg-coral/10 blur-3xl" />
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-24">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-bold text-coral shadow-sm">
            <Sparkles className="size-4" />
            اسباب‌بازی‌های فصل جدید رسیدند
          </div>
          <h1 className="mt-6 max-w-3xl text-5xl font-black tracking-tight text-ink sm:text-6xl lg:text-7xl">
            دنیای شاد اسباب‌بازی‌ها برای کودکان
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/65">
            در PlayNest بهترین اسباب‌بازی‌های آموزشی، فکری و سرگرم‌کننده را
            برای کودکان با خریدی ساده و مطمئن پیدا کنید.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" variant="coral">
              <Link href="#products">
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
              محصولات ایمن و منتخب
            </div>
            <div className="flex items-center gap-2">
              <Gift className="size-5 text-coral" />
              گزینه‌های مناسب هدیه
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="rounded-[2.5rem] bg-white p-5 shadow-soft">
            <div className="relative min-h-[26rem] overflow-hidden rounded-[2rem] bg-gradient-to-br from-skysoft via-cream to-coral/20 p-6">
              <div className="absolute right-8 top-8 rounded-3xl bg-white/80 px-4 py-3 text-sm font-bold text-ink shadow-sm">
                امتیاز ۴.۹ از خریداران
              </div>
              <div className="absolute bottom-8 left-8 right-8 rounded-3xl bg-white/85 p-5 shadow-soft backdrop-blur">
                <p className="text-sm font-bold uppercase tracking-wide text-coral">
                  بسته پیشنهادی
                </p>
                <h2 className="mt-2 text-2xl font-black text-ink">
                  ست ساختنی خلاقانه
                </h2>
                <p className="mt-2 text-sm leading-6 text-ink/60">
                  ترکیبی از بلوک، پازل و ابزارهای کوچک برای بازی و یادگیری.
                </p>
              </div>
              <div className="absolute left-10 top-20 size-28 rotate-12 rounded-3xl bg-sunshine shadow-soft" />
              <div className="absolute right-20 top-32 size-24 -rotate-12 rounded-full bg-mint shadow-soft" />
              <div className="absolute bottom-36 left-28 size-20 rounded-2xl bg-coral shadow-soft" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
