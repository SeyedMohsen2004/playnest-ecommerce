import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";

export function NewsletterSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-6 sm:px-6 lg:px-8" id="offers">
      <div className="overflow-hidden rounded-[2rem] bg-gradient-to-br from-coral via-orange-400 to-sunshine p-8 text-white shadow-soft sm:p-10 lg:p-12">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-white/75 sm:text-[0.8125rem]">
              پیشنهادهای IpakToys
            </p>
            <h2 className="mt-2 text-xl font-black leading-8 tracking-tight sm:text-2xl sm:leading-9">
              پیشنهادهای ویژه و ایده‌های هدیه را زودتر ببینید.
            </h2>
            <p className="mt-3 max-w-2xl text-[0.8125rem] leading-6 text-white/80 sm:text-sm sm:leading-7">
              با عضویت در خبرنامه، از بردگیم‌های جدید، تخفیف‌ها و پیشنهادهای
              مناسب خانواده و دورهمی باخبر شوید.
            </p>
          </div>
          <form className="rounded-[2.2rem] border border-white/55 bg-white/22 p-2.5 shadow-soft backdrop-blur dark:border-white/20 dark:bg-slate-950/20 sm:p-3">
            <div className="flex flex-col gap-2.5 rounded-[1.75rem] bg-white/88 p-2.5 shadow-sm ring-1 ring-white/70 dark:bg-slate-950/30 dark:ring-white/15 sm:flex-row sm:items-center">
              <label className="sr-only" htmlFor="newsletter-email">
                آدرس ایمیل
              </label>
              <div className="flex min-h-12 flex-1 items-center gap-3 rounded-2xl border border-coral/15 bg-cream/75 px-4 text-ink transition focus-within:border-coral/55 focus-within:bg-white focus-within:shadow-[0_12px_34px_rgba(255,93,108,0.18)] focus-within:ring-2 focus-within:ring-coral/25 dark:border-white/15 dark:bg-slate-900/55 dark:text-slate-50 dark:focus-within:border-sunshine/70 dark:focus-within:bg-slate-900/70 dark:focus-within:ring-sunshine/35 sm:min-h-14 sm:px-5">
                <Mail className="size-5 shrink-0 text-coral dark:text-sunshine" />
                <input
                  className="newsletter-email-input w-full rounded-xl border-0 bg-transparent px-1 py-2 text-right text-sm font-semibold text-ink outline-none placeholder:text-ink/50 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-50 dark:placeholder:text-slate-300/70"
                  id="newsletter-email"
                  placeholder="parent@example.com"
                  type="email"
                />
              </div>
              <Button
                className="h-12 w-full rounded-2xl px-7 shadow-glow sm:h-14 sm:w-auto"
                type="button"
                variant="coral"
              >
                عضویت
              </Button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
