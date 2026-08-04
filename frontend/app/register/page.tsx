"use client";

import { useRouter } from "next/navigation";
import {
  useEffect,
  useState,
  type ChangeEventHandler,
  type FormEvent,
} from "react";

import {
  getFriendlyAuthError,
  useAuth,
} from "@/components/providers/auth-provider";
import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";
import { APIError } from "@/lib/api/client";

export default function RegisterPage() {
  const router = useRouter();
  const { register, resendRegistration, verifyRegistration } = useAuth();
  const [phase, setPhase] = useState<"details" | "verify">("details");
  const [formData, setFormData] = useState({
    phone_number: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [code, setCode] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setInterval(() => {
      setCooldown((current) => Math.max(0, current - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  function updateField(field: keyof typeof formData, value: string) {
    setFormData((current) => ({ ...current, [field]: value }));
  }

  function applyRetryAfter(error: unknown) {
    if (error instanceof APIError && error.data && typeof error.data === "object") {
      const retryAfter = (error.data as { retry_after?: unknown }).retry_after;
      if (typeof retryAfter === "number") setCooldown(retryAfter);
    }
  }

  async function submitDetails(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setMessage("");
    if (formData.password !== formData.password_confirm) {
      setErrorMessage("رمز عبور و تکرار آن یکسان نیستند.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await register({
        phone_number: formData.phone_number.trim(),
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        password: formData.password,
        password_confirm: formData.password_confirm,
      });
      setCooldown(response.retry_after);
      setFormData((current) => ({
        ...current,
        password: "",
        password_confirm: "",
      }));
      setMessage(response.message);
      setPhase("verify");
    } catch (error) {
      applyRetryAfter(error);
      setErrorMessage(
        getFriendlyAuthError(
          error,
          "ثبت‌نام انجام نشد. لطفاً اطلاعات را بررسی کنید.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitVerification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setMessage("");
    setIsSubmitting(true);
    try {
      await verifyRegistration({
        phone_number: formData.phone_number.trim(),
        code: code.trim(),
      });
      setCode("");
      router.push("/");
    } catch (error) {
      setErrorMessage(
        getFriendlyAuthError(error, "کد تأیید نامعتبر یا منقضی شده است."),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function resend() {
    setErrorMessage("");
    setMessage("");
    setIsSubmitting(true);
    try {
      const response = await resendRegistration({
        phone_number: formData.phone_number.trim(),
      });
      setCooldown(response.retry_after);
      setMessage(response.message);
    } catch (error) {
      applyRetryAfter(error);
      setErrorMessage(
        getFriendlyAuthError(error, "ارسال دوباره کد امکان‌پذیر نیست."),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      description={
        phase === "details"
          ? "برای ایجاد حساب، اطلاعات زیر را وارد کنید."
          : `کد ارسال‌شده به ${formData.phone_number} را وارد کنید.`
      }
      footerHref="/login"
      footerLink="وارد شوید"
      footerText="قبلاً ثبت‌نام کرده‌اید؟"
      title={phase === "details" ? "ثبت‌نام در IpakToys" : "تأیید شماره موبایل"}
    >
      {phase === "details" ? (
        <form className="space-y-4" onSubmit={submitDetails}>
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
          <StatusMessages error={errorMessage} message={message} />
          <Button className="w-full" disabled={isSubmitting} type="submit" variant="coral">
            {isSubmitting ? "در حال ثبت‌نام..." : "ادامه و دریافت کد"}
          </Button>
        </form>
      ) : (
        <form className="space-y-4" onSubmit={submitVerification}>
          <Field
            label="کد شش‌رقمی"
            ltr
            onChange={(event) => setCode(event.target.value)}
            placeholder="123456"
            type="text"
            value={code}
          />
          <StatusMessages error={errorMessage} message={message} />
          <Button className="w-full" disabled={isSubmitting} type="submit" variant="coral">
            {isSubmitting ? "در حال بررسی..." : "تأیید و ورود"}
          </Button>
          <Button
            className="w-full"
            disabled={isSubmitting || cooldown > 0}
            onClick={resend}
            type="button"
            variant="outline"
          >
            {cooldown > 0 ? `ارسال دوباره تا ${cooldown} ثانیه` : "ارسال دوباره کد"}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}

function StatusMessages({ error, message }: { error: string; message: string }) {
  return (
    <>
      {error ? (
        <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold leading-7 text-rose-700">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold leading-7 text-emerald-700">
          {message}
        </p>
      ) : null}
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
