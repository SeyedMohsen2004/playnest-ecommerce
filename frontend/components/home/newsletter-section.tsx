import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";

export function NewsletterSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-6 sm:px-6 lg:px-8" id="offers">
      <div className="overflow-hidden rounded-[2rem] bg-gradient-to-br from-coral via-orange-400 to-sunshine p-8 text-white shadow-soft sm:p-10 lg:p-12">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-white/75">
              پیشنهادهای IpakToys
            </p>
            <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
              پیشنهادهای ویژه و ایده‌های هدیه را زودتر ببینید.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-white/80">
              با عضویت در خبرنامه، از بردگیم‌های جدید، تخفیف‌ها و پیشنهادهای
              مناسب خانواده و دورهمی باخبر شوید.
            </p>
          </div>
          <form className="rounded-[2.2rem] border border-white/55 bg-white/22 p-2.5 shadow-soft backdrop-blur dark:border-white/12 dark:bg-white/10 sm:p-3">
            <div className="flex flex-col gap-2.5 rounded-[1.75rem] bg-white/88 p-2.5 shadow-sm ring-1 ring-white/70 dark:bg-white/10 dark:ring-white/10 sm:flex-row sm:items-center">
              <label className="sr-only" htmlFor="newsletter-email">
                آدرس ایمیل
              </label>
              <div className="flex min-h-13 flex-1 items-center gap-3 rounded-[1.35rem] border border-coral/12 bg-cream/75 px-4 text-ink transition focus-within:border-coral/45 focus-within:bg-white focus-within:shadow-[0_12px_34px_rgba(255,93,108,0.18)] focus-within:ring-2 focus-within:ring-coral/20 dark:border-white/10 dark:bg-[rgb(var(--surface)/0.72)] dark:text-white dark:focus-within:border-sunshine/45 dark:focus-within:bg-white/12 dark:focus-within:ring-sunshine/25 sm:min-h-14 sm:px-5">
                <Mail className="size-5 shrink-0 text-coral dark:text-sunshine" />
                <input
                  className="w-full bg-transparent text-right text-sm font-semibold text-ink outline-none placeholder:text-ink/45 dark:text-white dark:placeholder:text-white/52"
                  id="newsletter-email"
                  placeholder="parent@example.com"
                  type="email"
                />
              </div>
              <Button
                className="h-13 rounded-[1.35rem] px-7 shadow-glow sm:h-14"
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
