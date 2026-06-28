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
    <div className="rounded-[1.75rem] bg-white/12 p-5 shadow-sm ring-1 ring-white/10 backdrop-blur transition hover:-translate-y-1 hover:bg-white/16">
      <span className="flex size-12 items-center justify-center rounded-2xl bg-white text-coral shadow-sm">
        <Icon className="size-6" aria-hidden="true" />
      </span>
      <h3 className="mt-4 text-lg font-black">{benefit.title}</h3>
      <p className="mt-2 text-sm leading-6 text-white/70">{benefit.description}</p>
    </div>
  );
}
