"use client";

import { Minus, Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { toPersianDigits } from "@/lib/format";

type QuantitySelectorProps = {
  initial?: number;
  value?: number;
  onChange?: (quantity: number) => void;
  disabled?: boolean;
  max?: number;
};

export function QuantitySelector({
  initial = 1,
  value,
  onChange,
  disabled = false,
  max,
}: QuantitySelectorProps) {
  const [internalQuantity, setInternalQuantity] = useState(initial);
  const quantity = value ?? internalQuantity;
  const maximumQuantity =
    typeof max === "number" && Number.isFinite(max) && max > 0
      ? Math.floor(max)
      : undefined;

  useEffect(() => {
    if (value === undefined) {
      setInternalQuantity(initial);
    }
  }, [initial, value]);

  useEffect(() => {
    if (maximumQuantity !== undefined && quantity > maximumQuantity) {
      if (value === undefined) {
        setInternalQuantity(maximumQuantity);
      }

      onChange?.(maximumQuantity);
    }
  }, [maximumQuantity, onChange, quantity, value]);

  function updateQuantity(nextQuantity: number) {
    const normalizedQuantity = Math.max(
      1,
      maximumQuantity !== undefined
        ? Math.min(nextQuantity, maximumQuantity)
        : nextQuantity,
    );

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
        disabled={disabled || quantity >= (maximumQuantity ?? Infinity)}
      >
        <Plus className="size-4" />
      </button>
    </div>
  );
}
