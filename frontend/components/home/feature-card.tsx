import type { LucideIcon } from "lucide-react";

import type { Benefit } from "@/types";

export function FeatureCard({
  benefit,
  icon: Icon,
}: {
  benefit: Benefit;
  icon: LucideIcon;
}) {
  return (
    <div className="rounded-3xl bg-white/10 p-5 backdrop-blur">
      <span className="flex size-12 items-center justify-center rounded-2xl bg-white text-ink">
        <Icon className="size-6" aria-hidden="true" />
      </span>
      <h3 className="mt-4 text-lg font-black">{benefit.title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/70">{benefit.description}</p>
    </div>
  );
}
