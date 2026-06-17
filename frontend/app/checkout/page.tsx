import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { cartItems } from "@/lib/mock-data";

const subtotal = cartItems.reduce(
  (sum, item) => sum + item.product.price * item.quantity,
  0,
);
const shipping = 50000;
const total = subtotal + shipping;

export default function CheckoutPage() {
  return (
    <>
      <PageHeader
        description="اطلاعات گیرنده و آدرس ارسال را وارد کنید. اتصال پرداخت در مرحله بعد فعال می‌شود."
        title="تسویه حساب"
      />
      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[1fr_24rem] lg:px-8">
        <form className="rounded-[2rem] bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-2xl font-black text-ink">اطلاعات ارسال</h2>
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <Field label="نام گیرنده" placeholder="نام و نام خانوادگی" />
            <Field label="شماره موبایل گیرنده" placeholder="09120000000" ltr />
            <Field label="کد پستی" placeholder="1234567890" ltr />
            <Field label="کد تخفیف" placeholder="OFF10" ltr />
          </div>
          <label className="mt-5 block">
            <span className="text-sm font-bold text-ink">آدرس ارسال</span>
            <textarea
              className="mt-2 min-h-36 w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3 text-sm leading-7 outline-none transition placeholder:text-ink/30 focus:border-coral"
              placeholder="استان، شهر، خیابان، پلاک و توضیحات لازم برای ارسال"
            />
          </label>
          <p className="mt-4 text-xs leading-6 text-ink/45">
            اطلاعات سفارش فعلا نمایشی است و پس از اتصال API برای ثبت سفارش ارسال
            می‌شود.
          </p>
        </form>

        <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-black text-ink">خلاصه پرداخت</h2>
          <div className="mt-6 space-y-4 text-sm">
            <Summary label="جمع سفارش" value={subtotal} />
            <Summary label="هزینه ارسال" value={shipping} />
            <Summary label="تخفیف" value={0} />
          </div>
          <div className="mt-6 border-t border-ink/10 pt-5">
            <Summary large label="مبلغ نهایی" value={total} />
          </div>
          <Button className="mt-6 w-full" type="button" variant="coral">
            ثبت سفارش و ادامه پرداخت
          </Button>
        </aside>
      </section>
    </>
  );
}

function Field({
  label,
  ltr = false,
  ...props
}: {
  label: string;
  placeholder: string;
  ltr?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-cream px-4 text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
        dir={ltr ? "ltr" : "rtl"}
        {...props}
      />
    </label>
  );
}

function Summary({
  label,
  value,
  large = false,
}: {
  label: string;
  value: number;
  large?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className={large ? "font-black text-ink" : "text-ink/60"}>
        {label}
      </span>
      <span className={large ? "text-xl font-black text-ink" : "font-bold text-ink"}>
        {new Intl.NumberFormat("fa-IR").format(value)} تومان
      </span>
    </div>
  );
}
