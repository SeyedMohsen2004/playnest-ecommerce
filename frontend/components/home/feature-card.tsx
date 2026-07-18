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
    <div className="rounded-[1.35rem] bg-white/12 p-4 shadow-sm ring-1 ring-white/10 backdrop-blur transition hover:-translate-y-1 hover:bg-white/16">
      <span className="flex size-10 items-center justify-center rounded-[1rem] bg-white text-coral shadow-sm">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <h3 className="mt-3 text-[0.9375rem] font-black">{benefit.title}</h3>
      <p className="mt-1.5 text-xs leading-6 text-white/70">{benefit.description}</p>
    </div>
  );
}
