export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-8 pt-10 sm:px-6 lg:px-8">
      <div className="rounded-[2.5rem] border border-white/70 bg-white/58 p-6 shadow-sm backdrop-blur sm:p-8">
      {eyebrow ? (
        <p className="text-sm font-bold uppercase tracking-wide text-coral">
          {eyebrow}
        </p>
      ) : null}
      <h1 className="mt-3 text-3xl font-black tracking-tight text-ink sm:text-4xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-4 max-w-2xl text-sm leading-7 text-ink/60">
          {description}
        </p>
      ) : null}
      </div>
    </section>
  );
}
