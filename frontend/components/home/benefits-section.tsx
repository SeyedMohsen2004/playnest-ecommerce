import { CreditCard, RotateCcw, ShieldCheck, Truck } from "lucide-react";

import { FeatureCard } from "@/components/home/feature-card";
import { benefits } from "@/lib/mock-data";

const icons = [ShieldCheck, Truck, RotateCcw, CreditCard];

export function BenefitsSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8" id="benefits">
      <div className="rounded-[2.5rem] bg-gradient-to-br from-ink via-[#24304f] to-grape p-6 text-white shadow-soft sm:p-8 lg:p-10">
        <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-sunshine">
              چرا خانواده‌ها IpakToys را انتخاب می‌کنند؟
            </p>
            <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
              از انتخاب بازی تا پرداخت، همراه مطمئن شما هستیم.
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {benefits.map((benefit, index) => (
              <FeatureCard
                benefit={benefit}
                icon={icons[index]}
                key={benefit.title}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
