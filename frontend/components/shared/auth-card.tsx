import Link from "next/link";
import type { ReactNode } from "react";

export function AuthCard({
  title,
  description,
  footerText,
  footerHref,
  footerLink,
  children,
}: {
  title: string;
  description: string;
  footerText: string;
  footerHref: string;
  footerLink: string;
  children: ReactNode;
}) {
  return (
    <section className="mx-auto flex min-h-[calc(100vh-12rem)] max-w-7xl items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="relative w-full max-w-md overflow-hidden rounded-[2.25rem] border border-white/75 bg-white/88 p-6 shadow-card backdrop-blur sm:p-8">
        <span className="pointer-events-none absolute -left-12 -top-12 size-32 rounded-full bg-coral/10 blur-2xl" />
        <p className="text-sm font-bold uppercase tracking-wide text-coral">
          IpakToys
        </p>
        <h1 className="relative mt-3 text-3xl font-black text-ink">{title}</h1>
        <p className="relative mt-3 text-sm leading-7 text-ink/60">
          {description}
        </p>
        <div className="relative mt-8">{children}</div>
        <p className="mt-6 text-center text-sm text-ink/60">
          {footerText}{" "}
          <Link className="font-bold text-coral" href={footerHref}>
            {footerLink}
          </Link>
        </p>
      </div>
    </section>
  );
}
