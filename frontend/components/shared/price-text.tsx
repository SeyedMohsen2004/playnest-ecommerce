import { formatToman } from "@/lib/format";
import { cn } from "@/lib/utils";

export function PriceText({
  amount,
  oldAmount,
  className,
}: {
  amount: number;
  oldAmount?: number | null;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-end gap-2", className)}>
      <span className="text-xl font-black text-ink">{formatToman(amount)}</span>
      {oldAmount && oldAmount > amount ? (
        <span className="pb-0.5 text-xs text-ink/35 line-through">
          {formatToman(oldAmount)}
        </span>
      ) : null}
    </div>
  );
}
