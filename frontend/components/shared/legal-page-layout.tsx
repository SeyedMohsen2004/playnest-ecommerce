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
      <section className="rounded-[2.5rem] bg-white p-6 shadow-soft sm:p-10">
        <p className="text-sm font-bold uppercase tracking-wide text-coral">
          PlayNest
        </p>
        <h1 className="mt-3 text-4xl font-black leading-tight text-ink sm:text-5xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-5 max-w-3xl text-sm leading-8 text-ink/60">
            {description}
          </p>
        ) : null}
        <div className="mt-10 space-y-6">{children}</div>
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
    <section className="rounded-[2rem] border border-ink/5 bg-cream/60 p-5 sm:p-6">
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
          <span className="mt-3 size-2 rounded-full bg-coral" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function DraftNotice() {
  return (
    <div className="rounded-[2rem] border border-coral/15 bg-coral/5 p-5 text-sm leading-8 text-ink/65">
      این متن به‌عنوان پیش‌نویس عمومی برای نسخه توسعه PlayNest آماده شده است و
      پیش از انتشار نهایی باید با اطلاعات واقعی، سیاست‌های اجرایی و تایید مالک
      کسب‌وکار به‌روزرسانی شود.
    </div>
  );
}
