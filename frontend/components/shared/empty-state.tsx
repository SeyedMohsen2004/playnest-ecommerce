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
    <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral">
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
