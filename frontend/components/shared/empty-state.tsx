import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
}) {
  return (
    <div className="rounded-[2.25rem] border border-dashed border-coral/20 bg-white/82 p-8 text-center shadow-card backdrop-blur">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral shadow-sm">
        <Icon className="size-8" aria-hidden="true" />
      </span>
      <h2 className="mt-5 text-2xl font-black text-ink">{title}</h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-ink/60">
        {description}
      </p>
      {actionLabel ? (
        <Button className="mt-6" variant="coral">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
