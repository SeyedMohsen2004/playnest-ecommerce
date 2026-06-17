"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ChangeEventHandler, type FormEvent } from "react";

import {
  getFriendlyAuthError,
  useAuth,
} from "@/components/providers/auth-provider";
import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      await login({
        phone_number: phoneNumber.trim(),
        password,
      });
      router.push("/products");
    } catch (error) {
      setErrorMessage(
        getFriendlyAuthError(error, "شماره موبایل یا رمز عبور اشتباه است."),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      description="برای مشاهده سفارش‌ها و ادامه خرید وارد حساب کاربری خود شوید."
      footerHref="/register"
      footerLink="ثبت‌نام کنید"
      footerText="حساب کاربری ندارید؟"
      title="ورود به حساب کاربری"
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <Field
          helper="شماره موبایل باید با ۰۹ شروع شود."
          label="شماره موبایل"
          onChange={(event) => setPhoneNumber(event.target.value)}
          placeholder="09120000000"
          type="tel"
          value={phoneNumber}
        />
        <Field
          helper="رمز عبور خود را وارد کنید."
          label="رمز عبور"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
          type="password"
          value={password}
        />

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
          {isSubmitting ? "در حال ورود..." : "ورود"}
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
  value: string;
  onChange: ChangeEventHandler<HTMLInputElement>;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-cream px-4 text-left text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
        dir="ltr"
        required
        {...props}
      />
      <span className="mt-2 block text-xs text-ink/45">{helper}</span>
    </label>
  );
}
