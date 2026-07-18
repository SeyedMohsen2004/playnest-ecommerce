import { CreditCard, RotateCcw, ShieldCheck, Truck } from "lucide-react";

import { FeatureCard } from "@/components/home/feature-card";
import { benefits } from "@/lib/mock-data";

const icons = [ShieldCheck, Truck, RotateCcw, CreditCard];

export function BenefitsSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 sm:py-11 lg:px-8" id="benefits">
      <div className="rounded-[2rem] bg-gradient-to-br from-ink via-[#24304f] to-grape p-5 text-white shadow-soft sm:p-6 lg:p-7">
        <div className="grid gap-5 lg:grid-cols-[0.72fr_1.28fr] lg:items-center">
          <div>
            <p className="text-[0.6875rem] font-bold uppercase tracking-wide text-sunshine sm:text-[0.71875rem]">
              چرا خانواده‌ها IpakToys را انتخاب می‌کنند؟
            </p>
            <h2 className="mt-2 text-lg font-black leading-7 tracking-tight sm:text-[1.375rem] sm:leading-8">
              از انتخاب بازی تا پرداخت، همراه مطمئن شما هستیم.
            </h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
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
