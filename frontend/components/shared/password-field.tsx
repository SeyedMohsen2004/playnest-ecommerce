"use client";

import { Eye, EyeOff } from "lucide-react";
import { useId, useState, type ChangeEventHandler } from "react";

export function PasswordField({
  label,
  helper,
  value,
  onChange,
}: {
  label: string;
  helper?: string;
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
}) {
  const inputId = useId();
  const [isVisible, setIsVisible] = useState(false);
  const visibilityLabel = isVisible
    ? "پنهان کردن رمز عبور"
    : "نمایش رمز عبور";

  return (
    <div>
      <label className="text-sm font-bold text-ink" htmlFor={inputId}>
        {label}
      </label>
      <span className="relative mt-2 block">
        <input
          className="h-12 w-full rounded-2xl border border-ink/10 bg-cream py-2 pl-12 pr-4 text-left text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
          dir="ltr"
          id={inputId}
          onChange={onChange}
          placeholder="••••••••"
          required
          type={isVisible ? "text" : "password"}
          value={value}
        />
        <button
          aria-label={visibilityLabel}
          className="absolute inset-y-1 left-1 flex size-10 items-center justify-center rounded-xl text-ink/50 transition hover:bg-white/70 hover:text-coral focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-coral focus-visible:ring-offset-1"
          onClick={() => setIsVisible((current) => !current)}
          type="button"
        >
          {isVisible ? (
            <EyeOff aria-hidden="true" className="size-5" />
          ) : (
            <Eye aria-hidden="true" className="size-5" />
          )}
        </button>
      </span>
      {helper ? (
        <span className="mt-2 block text-xs text-ink/45">{helper}</span>
      ) : null}
    </div>
  );
}
