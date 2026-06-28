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
          <form className="rounded-[2rem] border border-white/70 bg-white/82 p-3 shadow-soft backdrop-blur dark:border-white/10 dark:bg-white/10 sm:p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <label className="sr-only" htmlFor="newsletter-email">
                آدرس ایمیل
              </label>
              <div className="flex min-h-14 flex-1 items-center gap-3 rounded-[1.4rem] border border-coral/10 bg-cream/80 px-4 text-ink shadow-sm transition focus-within:border-white/80 focus-within:bg-white focus-within:shadow-glow focus-within:ring-2 focus-within:ring-white/70 dark:border-white/10 dark:bg-white/10 dark:text-white dark:focus-within:border-coral/50 dark:focus-within:bg-white/15 dark:focus-within:ring-coral/35 sm:px-5">
                <Mail className="size-5 shrink-0 text-coral dark:text-sunshine" />
                <input
                  className="w-full bg-transparent text-sm font-semibold text-ink outline-none placeholder:text-ink/45 dark:text-white dark:placeholder:text-white/48"
                  id="newsletter-email"
                  placeholder="parent@example.com"
                  type="email"
                />
              </div>
              <Button
                className="h-14 rounded-[1.4rem] px-7"
                type="button"
                variant="default"
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
