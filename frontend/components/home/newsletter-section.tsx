import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";

export function NewsletterSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 pt-6 sm:px-6 lg:px-8" id="offers">
      <div className="overflow-hidden rounded-[2rem] bg-gradient-to-br from-coral via-orange-400 to-sunshine p-8 text-white shadow-soft sm:p-10 lg:p-12">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-white/75">
              PlayNest offers
            </p>
            <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
              Get playful deals and gift ideas in your inbox.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-white/80">
              Join the PlayNest list for seasonal toy picks, new arrivals, and
              family-friendly offers.
            </p>
          </div>
          <form className="rounded-3xl bg-white p-3 shadow-soft">
            <div className="flex flex-col gap-3 sm:flex-row">
              <label className="sr-only" htmlFor="newsletter-email">
                Email address
              </label>
              <div className="flex min-h-12 flex-1 items-center gap-3 rounded-full bg-cream px-4 text-ink">
                <Mail className="size-5 text-coral" />
                <input
                  className="w-full bg-transparent text-sm outline-none placeholder:text-ink/40"
                  id="newsletter-email"
                  placeholder="parent@example.com"
                  type="email"
                />
              </div>
              <Button type="button" variant="default">
                Join now
              </Button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
