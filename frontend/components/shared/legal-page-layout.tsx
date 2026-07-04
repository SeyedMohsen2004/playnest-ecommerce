import type { ReactNode } from "react";

export function LegalPageLayout({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="relative overflow-hidden rounded-[2.5rem] border border-white/70 bg-white/86 p-6 shadow-card backdrop-blur sm:p-10">
        <span className="pointer-events-none absolute -left-16 -top-16 size-40 rounded-full bg-sunshine/20 blur-2xl" />
        <p className="text-sm font-bold uppercase tracking-wide text-coral">
          IpakToys
        </p>
        <h1 className="mt-3 text-3xl font-black leading-tight text-ink sm:text-4xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-5 max-w-3xl text-sm leading-8 text-ink/60">
            {description}
          </p>
        ) : null}
        <div className="relative mt-10 space-y-6">{children}</div>
      </section>
    </main>
  );
}

export function InfoSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-white/70 bg-cream/70 p-5 shadow-sm sm:p-6">
      <h2 className="text-xl font-black text-ink">{title}</h2>
      <div className="mt-3 text-sm leading-8 text-ink/65">{children}</div>
    </section>
  );
}

export function InfoList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li className="flex gap-3" key={item}>
          <span className="mt-3 size-2 shrink-0 rounded-full bg-coral" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function DraftNotice() {
  return (
    <div className="rounded-[2rem] border border-coral/15 bg-coral/5 p-5 text-sm leading-8 text-ink/65 shadow-sm">
      این متن به‌عنوان پیش‌نویس عمومی برای نسخه توسعه IpakToys آماده شده است و
      پیش از انتشار نهایی باید با اطلاعات واقعی، سیاست‌های اجرایی و تایید مالک
      کسب‌وکار به‌روزرسانی شود.
    </div>
  );
}
