import Link from "next/link";

import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <AuthCard
      description="برای مشاهده سفارش‌ها و ادامه خرید وارد حساب کاربری خود شوید."
      footerHref="/register"
      footerLink="ثبت‌نام کنید"
      footerText="حساب کاربری ندارید؟"
      title="ورود به حساب کاربری"
    >
      <form className="space-y-5">
        <Field
          helper="شماره موبایل باید با ۰۹ شروع شود."
          label="شماره موبایل"
          placeholder="09120000000"
          type="tel"
        />
        <Field
          helper="رمز عبور خود را وارد کنید."
          label="رمز عبور"
          placeholder="••••••••"
          type="password"
        />
        <Button className="w-full" type="button" variant="coral">
          ورود
        </Button>
        <Link className="block text-center text-sm font-bold text-coral" href="#">
          رمز عبور را فراموش کرده‌اید؟
        </Link>
      </form>
    </AuthCard>
  );
}

function Field({
  label,
  helper,
  ...props
}: {
  label: string;
  helper: string;
  placeholder: string;
  type: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-cream px-4 text-left text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
        dir="ltr"
        {...props}
      />
      <span className="mt-2 block text-xs text-ink/45">{helper}</span>
    </label>
  );
}
