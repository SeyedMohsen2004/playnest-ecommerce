"use client";

import { Minus, Plus } from "lucide-react";
import { useState } from "react";

export function QuantitySelector({ initial = 1 }: { initial?: number }) {
  const [quantity, setQuantity] = useState(initial);

  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-ink/10 bg-white p-1 shadow-sm">
      <button
        type="button"
        className="flex size-9 items-center justify-center rounded-full bg-cream text-ink transition hover:bg-coral hover:text-white"
        onClick={() => setQuantity((current) => Math.max(1, current - 1))}
        aria-label="کم کردن تعداد"
      >
        <Minus className="size-4" />
      </button>
      <span className="min-w-8 text-center text-sm font-black text-ink">
        {new Intl.NumberFormat("fa-IR").format(quantity)}
      </span>
      <button
        type="button"
        className="flex size-9 items-center justify-center rounded-full bg-cream text-ink transition hover:bg-coral hover:text-white"
        onClick={() => setQuantity((current) => current + 1)}
        aria-label="زیاد کردن تعداد"
      >
        <Plus className="size-4" />
      </button>
    </div>
  );
}
