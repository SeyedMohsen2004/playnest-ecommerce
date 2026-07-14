import { cn } from "@/lib/utils";
import type { OrderStatus } from "@/types";

const statusMap: Record<OrderStatus, { label: string; className: string }> = {
  pending: {
    label: "در انتظار پرداخت",
    className: "bg-amber-100 text-amber-700",
  },
  payment_failed: {
    label: "پرداخت ناموفق",
    className: "bg-rose-100 text-rose-700",
  },
  paid: {
    label: "پرداخت موفق، در انتظار تایید",
    className: "bg-emerald-100 text-emerald-700",
  },
  processing: {
    label: "در حال آماده‌سازی",
    className: "bg-sky-100 text-sky-700",
  },
  shipped: {
    label: "ارسال شده",
    className: "bg-violet-100 text-violet-700",
  },
  delivered: {
    label: "تحویل داده شده",
    className: "bg-mint/30 text-emerald-800",
  },
  cancelled: {
    label: "لغو شده",
    className: "bg-rose-100 text-rose-700",
  },
};

export function StatusBadge({ status }: { status: OrderStatus }) {
  const current = statusMap[status];

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-3 py-1 text-xs font-bold",
        current.className,
      )}
    >
      {current.label}
    </span>
  );
}
