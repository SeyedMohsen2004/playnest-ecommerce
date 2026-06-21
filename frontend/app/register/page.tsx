"use client";

import { useRouter } from "next/navigation";
import { useState, type ChangeEventHandler, type FormEvent } from "react";

import {
  getFriendlyAuthError,
  useAuth,
} from "@/components/providers/auth-provider";
import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    phone_number: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: keyof typeof formData, value: string) {
    setFormData((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");

    if (formData.password !== formData.password_confirm) {
      setErrorMessage("رمز عبور و تکرار آن یکسان نیستند.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        phone_number: formData.phone_number.trim(),
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        password: formData.password,
        password_confirm: formData.password_confirm,
      });
      router.push(
        `/verify-otp?phone_number=${encodeURIComponent(
          formData.phone_number.trim(),
        )}`,
      );
    } catch (error) {
      setErrorMessage(
        getFriendlyAuthError(
          error,
          "ثبت‌نام انجام نشد. لطفا اطلاعات را بررسی کنید.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      description="کد تایید برای شماره موبایل شما ارسال می‌شود و پس از تایید، حساب فعال خواهد شد."
      footerHref="/login"
      footerLink="وارد شوید"
      footerText="قبلا ثبت‌نام کرده‌اید؟"
      title="ثبت‌نام در IpakToys"
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Field
          label="شماره موبایل"
          ltr
          onChange={(event) => updateField("phone_number", event.target.value)}
          placeholder="09121111111"
          type="tel"
          value={formData.phone_number}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label="نام"
            onChange={(event) => updateField("first_name", event.target.value)}
            placeholder="نام"
            type="text"
            value={formData.first_name}
          />
          <Field
            label="نام خانوادگی"
            onChange={(event) => updateField("last_name", event.target.value)}
            placeholder="نام خانوادگی"
            type="text"
            value={formData.last_name}
          />
        </div>
        <Field
          label="رمز عبور"
          ltr
          onChange={(event) => updateField("password", event.target.value)}
          placeholder="••••••••"
          type="password"
          value={formData.password}
        />
        <Field
          label="تکرار رمز عبور"
          ltr
          onChange={(event) =>
            updateField("password_confirm", event.target.value)
          }
          placeholder="••••••••"
          type="password"
          value={formData.password_confirm}
        />
        <p className="rounded-2xl bg-skysoft px-4 py-3 text-xs leading-6 text-ink/60">
          کد تایید برای شماره موبایل شما ارسال می‌شود. در محیط توسعه، کد OTP در
          لاگ بک‌اند چاپ می‌شود.
        </p>

        {errorMessage ? (
          <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold leading-7 text-rose-700">
            {errorMessage}
          </p>
        ) : null}

        <Button
          className="w-full"
          disabled={isSubmitting}
          type="submit"
          variant="coral"
        >
          {isSubmitting ? "در حال ثبت‌نام..." : "ثبت‌نام"}
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
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
  ltr?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-cream px-4 text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
        dir={ltr ? "ltr" : "rtl"}
        required
        {...props}
      />
    </label>
  );
}
