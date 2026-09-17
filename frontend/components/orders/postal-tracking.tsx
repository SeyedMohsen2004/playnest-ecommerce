import type { Order } from "@/types/api";

export function PostalTracking({
  order,
}: {
  order: Pick<Order, "status" | "postal_tracking_code">;
}) {
  if (
    !["shipped", "delivered"].includes(order.status) ||
    !order.postal_tracking_code?.trim()
  ) {
    return null;
  }

  return (
    <section
      aria-label="کد رهگیری پستی"
      className="min-w-0 rounded-3xl bg-sky-50 p-5 text-right dark:bg-sky-950/35"
      dir="rtl"
    >
      <h3 className="text-sm font-black text-ink dark:text-white">
        کد رهگیری پستی
      </h3>
      <p
        className="mt-2 font-mono text-base leading-7 text-ink [overflow-wrap:anywhere] dark:text-white"
        dir="ltr"
      >
        {order.postal_tracking_code}
      </p>
    </section>
  );
}
