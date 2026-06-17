"use client";

import { Minus, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { toPersianDigits } from "@/lib/format";

type QuantitySelectorProps = {
  initial?: number;
  value?: number;
  onChange?: (quantity: number) => void;
  disabled?: boolean;
};

export function QuantitySelector({
  initial = 1,
  value,
  onChange,
  disabled = false,
}: QuantitySelectorProps) {
  const [internalQuantity, setInternalQuantity] = useState(initial);
  const quantity = value ?? internalQuantity;

  useEffect(() => {
    if (value === undefined) {
      setInternalQuantity(initial);
    }
  }, [initial, value]);

  function updateQuantity(nextQuantity: number) {
    const normalizedQuantity = Math.max(1, nextQuantity);

    if (value === undefined) {
      setInternalQuantity(normalizedQuantity);
    }

    onChange?.(normalizedQuantity);
  }

  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-ink/10 bg-white p-1 shadow-sm">
      <button
        type="button"
        className="flex size-9 items-center justify-center rounded-full bg-cream text-ink transition hover:bg-coral hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        onClick={() => updateQuantity(quantity - 1)}
        aria-label="کم کردن تعداد"
        disabled={disabled || quantity <= 1}
      >
        <Minus className="size-4" />
      </button>
      <span className="min-w-8 text-center text-sm font-black text-ink">
        {toPersianDigits(quantity)}
      </span>
      <button
        type="button"
        className="flex size-9 items-center justify-center rounded-full bg-cream text-ink transition hover:bg-coral hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        onClick={() => updateQuantity(quantity + 1)}
        aria-label="زیاد کردن تعداد"
        disabled={disabled}
      >
        <Plus className="size-4" />
      </button>
    </div>
  );
}
