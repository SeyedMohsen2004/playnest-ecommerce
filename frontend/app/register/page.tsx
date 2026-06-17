import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";

export default function RegisterPage() {
  return (
    <AuthCard
      description="پس از ثبت‌نام، کد تایید پیامکی برای فعال‌سازی حساب لازم است."
      footerHref="/login"
      footerLink="وارد شوید"
      footerText="قبلا ثبت‌نام کرده‌اید؟"
      title="ثبت‌نام در PlayNest"
    >
      <form className="space-y-4">
        <Field label="شماره موبایل" placeholder="09121111111" type="tel" ltr />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="نام" placeholder="نام" type="text" />
          <Field label="نام خانوادگی" placeholder="نام خانوادگی" type="text" />
        </div>
        <Field label="رمز عبور" placeholder="••••••••" type="password" ltr />
        <Field label="تکرار رمز عبور" placeholder="••••••••" type="password" ltr />
        <p className="rounded-2xl bg-skysoft px-4 py-3 text-xs leading-6 text-ink/60">
          بعد از ثبت‌نام، مرحله تایید کد OTP برای فعال‌سازی حساب نمایش داده می‌شود.
        </p>
        <Button className="w-full" type="button" variant="coral">
          ثبت‌نام
        </Button>
      </form>
    </AuthCard>
  );
}

function Field({
  label,
  ltr = false,
  ...props
}: {
  label: string;
  placeholder: string;
  type: string;
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
