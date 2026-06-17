import { cn } from "@/lib/utils";

const formatter = new Intl.NumberFormat("fa-IR");

export function PriceText({
  amount,
  oldAmount,
  className,
}: {
  amount: number;
  oldAmount?: number;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-end gap-2", className)}>
      <span className="text-xl font-black text-ink">
        {formatter.format(amount)}
      </span>
      <span className="pb-0.5 text-xs font-semibold text-ink/45">تومان</span>
      {oldAmount ? (
        <span className="pb-0.5 text-xs text-ink/35 line-through">
          {formatter.format(oldAmount)} تومان
        </span>
      ) : null}
    </div>
  );
}
