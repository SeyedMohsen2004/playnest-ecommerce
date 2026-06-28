"use client";

import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/components/providers/theme-provider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      aria-label={isDark ? "فعال کردن حالت روشن" : "فعال کردن حالت تیره"}
      className="flex size-10 items-center justify-center rounded-2xl bg-white/70 text-ink shadow-sm ring-1 ring-white/70 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10"
      onClick={toggleTheme}
      type="button"
    >
      {isDark ? <Sun className="size-5" /> : <Moon className="size-5" />}
    </button>
  );
}
