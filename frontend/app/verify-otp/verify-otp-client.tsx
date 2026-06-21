"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  getFriendlyAuthError,
  useAuth,
} from "@/components/providers/auth-provider";
import { AuthCard } from "@/components/shared/auth-card";
import { Button } from "@/components/ui/button";

export function VerifyOtpClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyOtp } = useAuth();
  const phoneNumber = searchParams.get("phone_number") || "";
  const [code, setCode] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");

    if (!phoneNumber) {
      setErrorMessage("شماره موبایل برای تایید حساب پیدا نشد.");
      return;
    }

    setIsSubmitting(true);

    try {
      await verifyOtp({
        phone_number: phoneNumber,
        code: code.trim(),
      });
      router.push("/");
    } catch (error) {
      setErrorMessage(
        getFriendlyAuthError(
          error,
          "کد تایید اشتباه است یا منقضی شده است.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthCard
      description="کد تایید ارسال‌شده را وارد کنید تا حساب IpakToys شما فعال شود."
      footerHref="/register"
      footerLink="اصلاح شماره موبایل"
      footerText="شماره را اشتباه وارد کرده‌اید؟"
      title="تایید شماره موبایل"
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="rounded-2xl bg-skysoft px-4 py-3 text-sm leading-7 text-ink/65">
          کد تایید برای شماره{" "}
          <span className="font-black text-ink" dir="ltr">
            {phoneNumber || "نامشخص"}
          </span>{" "}
          ارسال شده است. در محیط توسعه، کد OTP در لاگ بک‌اند چاپ می‌شود.
        </div>

        <label className="block">
          <span className="text-sm font-bold text-ink">کد تایید</span>
          <input
            className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-cream px-4 text-center text-lg font-black tracking-[0.4em] outline-none transition placeholder:text-ink/30 focus:border-coral"
            dir="ltr"
            inputMode="numeric"
            maxLength={6}
            onChange={(event) => setCode(event.target.value)}
            placeholder="123456"
            required
            type="text"
            value={code}
          />
        </label>

        {errorMessage ? (
          <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold leading-7 text-rose-700">
            {errorMessage}
          </p>
        ) : null}

        <Button
          className="w-full"
          disabled={isSubmitting || !phoneNumber}
          type="submit"
          variant="coral"
        >
          {isSubmitting ? "در حال تایید..." : "تایید و ورود"}
        </Button>
        <Button className="w-full" disabled type="button" variant="outline">
          ارسال دوباره کد به‌زودی فعال می‌شود
        </Button>
      </form>
    </AuthCard>
  );
}
