"use client";

import { LogIn, PackageOpen, ShoppingBag } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ChangeEventHandler,
  type FormEvent,
} from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { getCart } from "@/lib/api/cart";
import { APIError } from "@/lib/api/client";
import { applyCoupon, createCheckoutOrder } from "@/lib/api/checkout";
import { getShippingRates } from "@/lib/api/shipping";
import { clearTokens, getAccessToken } from "@/lib/auth/token-storage";
import { formatToman, toPersianDigits } from "@/lib/format";
import { getProductPrice } from "@/lib/product-display";
import type {
  Cart,
  CartItem,
  CheckoutResponse,
  CouponPreviewResponse,
  ShippingRatesResponse,
  ShippingZone,
} from "@/types/api";

type CheckoutFormData = {
  recipient_name: string;
  recipient_phone: string;
  postal_code: string;
  shipping_address: string;
  shipping_zone: ShippingZone | "";
  coupon_code: string;
};

type ValidationErrors = Partial<Record<keyof CheckoutFormData, string>>;

const initialFormData: CheckoutFormData = {
  recipient_name: "",
  recipient_phone: "",
  postal_code: "",
  shipping_address: "",
  shipping_zone: "",
  coupon_code: "",
};

const shippingZoneOrder: ShippingZone[] = ["tabriz", "nationwide"];

export default function CheckoutPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [shippingRates, setShippingRates] =
    useState<ShippingRatesResponse | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {},
  );
  const [couponPreview, setCouponPreview] =
    useState<CouponPreviewResponse | null>(null);
  const [appliedCouponCode, setAppliedCouponCode] = useState("");
  const [couponMessage, setCouponMessage] = useState("");
  const [couponTone, setCouponTone] = useState<"success" | "error">("success");
  const [pageError, setPageError] = useState("");
  const [isCartLoading, setIsCartLoading] = useState(true);
  const [isCouponLoading, setIsCouponLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleUnauthorized = useCallback(() => {
    clearTokens();
    logout();
    setPageError("نشست شما منقضی شده است. لطفا دوباره وارد شوید.");
  }, [logout]);

  const loadCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      setIsCartLoading(false);
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      setIsCartLoading(false);
      return;
    }

    setIsCartLoading(true);
    setPageError("");

    try {
      const [loadedCart, loadedShippingRates] = await Promise.all([
        getCart(accessToken),
        getShippingRates(),
      ]);
      setCart(loadedCart);
      setShippingRates(loadedShippingRates);
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setPageError("خطا در دریافت سبد خرید. لطفا کمی بعد دوباره تلاش کنید.");
      }
    } finally {
      setIsCartLoading(false);
    }
  }, [handleUnauthorized, isAuthenticated]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    loadCart();
  }, [isAuthLoading, loadCart]);

  const summary = useMemo(
    () =>
      buildSummary(
        cart,
        couponPreview,
        formData.shipping_zone && shippingRates
          ? shippingRates[formData.shipping_zone].fee
          : 0,
      ),
    [cart, couponPreview, formData.shipping_zone, shippingRates],
  );
  const items = cart?.items || [];

  function updateField<Field extends keyof CheckoutFormData>(
    field: Field,
    value: CheckoutFormData[Field],
  ) {
    setFormData((current) => ({ ...current, [field]: value }));
    setValidationErrors((current) => ({ ...current, [field]: undefined }));
  }

  async function handleApplyCoupon() {
    const code = formData.coupon_code.trim();
    setCouponMessage("");

    if (!code) {
      setCouponTone("error");
      setCouponMessage("لطفاً کد تخفیف را وارد کنید.");
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    setIsCouponLoading(true);

    try {
      const response = await applyCoupon(accessToken, code);
      setCouponPreview(response);
      setAppliedCouponCode(code);
      setCouponTone("success");
      setCouponMessage("کد تخفیف با موفقیت اعمال شد.");
    } catch (error) {
      if (process.env.NODE_ENV !== "production") {
        console.error("Apply coupon error:", error);
      }

      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setCouponPreview(null);
        setAppliedCouponCode("");
        setCouponTone("error");
        setCouponMessage("کد تخفیف معتبر نیست یا شرایط استفاده را ندارد.");
      }
    } finally {
      setIsCouponLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPageError("");

    const errors = validateCheckoutForm(formData);
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    if (!formData.shipping_zone) {
      return;
    }

    const accessToken = getAccessToken();

    if (!accessToken) {
      handleUnauthorized();
      return;
    }

    const couponCode = appliedCouponCode || formData.coupon_code.trim();
    setIsSubmitting(true);

    try {
      const response = await createCheckoutOrder(accessToken, {
        shipping_address: formData.shipping_address.trim(),
        postal_code: normalizeDigits(formData.postal_code).trim(),
        recipient_name: formData.recipient_name.trim(),
        recipient_phone: normalizeDigits(formData.recipient_phone).trim(),
        shipping_zone: formData.shipping_zone,
        ...(couponCode ? { coupon_code: couponCode } : {}),
      });
      const orderId = extractOrderId(response);

      if (!orderId) {
        throw new Error("Checkout response did not include an order id.");
      }

      router.push(`/payment/${orderId}`);
    } catch (error) {
      if (process.env.NODE_ENV !== "production") {
        console.error("Checkout order error:", error);
      }

      if (error instanceof APIError && error.status === 401) {
        handleUnauthorized();
      } else {
        setPageError("خطا در ثبت سفارش. لطفاً اطلاعات را بررسی کنید.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        description="اطلاعات گیرنده و آدرس ارسال را وارد کنید. پس از ثبت سفارش به مرحله پرداخت هدایت می‌شوید."
        title="تسویه حساب"
      />
      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-16 sm:px-6 lg:grid-cols-[1fr_24rem] lg:px-8">
        {isAuthLoading || isCartLoading ? (
          <div className="lg:col-span-2 rounded-[2rem] bg-white p-10 text-center text-sm font-black text-ink/60 shadow-sm">
            در حال آماده‌سازی تسویه حساب...
          </div>
        ) : !isAuthenticated ? (
          <div className="lg:col-span-2">
            <LoginRequiredState />
          </div>
        ) : items.length === 0 ? (
          <div className="lg:col-span-2">
            <EmptyCartState />
          </div>
        ) : (
          <>
            <form
              className="rounded-[2rem] bg-white p-6 shadow-sm sm:p-8"
              onSubmit={handleSubmit}
            >
              <h2 className="text-2xl font-black text-ink">اطلاعات ارسال</h2>
              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                <Field
                  error={validationErrors.recipient_name}
                  label="نام گیرنده"
                  onChange={(event) =>
                    updateField("recipient_name", event.target.value)
                  }
                  placeholder="نام و نام خانوادگی"
                  value={formData.recipient_name}
                />
                <Field
                  error={validationErrors.recipient_phone}
                  label="شماره موبایل گیرنده"
                  ltr
                  onChange={(event) =>
                    updateField("recipient_phone", event.target.value)
                  }
                  placeholder="09120000000"
                  value={formData.recipient_phone}
                />
                <Field
                  error={validationErrors.postal_code}
                  label="کد پستی"
                  ltr
                  onChange={(event) =>
                    updateField("postal_code", event.target.value)
                  }
                  placeholder="1234567890"
                  value={formData.postal_code}
                />
                <div>
                  <Field
                    error={validationErrors.coupon_code}
                    label="کد تخفیف"
                    ltr
                    onChange={(event) =>
                      updateField("coupon_code", event.target.value)
                    }
                    placeholder="OFF10"
                    value={formData.coupon_code}
                  />
                  <Button
                    className="mt-3 w-full"
                    disabled={isCouponLoading}
                    onClick={handleApplyCoupon}
                    type="button"
                    variant="outline"
                  >
                    {isCouponLoading
                      ? "در حال بررسی کد..."
                      : "اعمال کد تخفیف"}
                  </Button>
                </div>
              </div>

              <fieldset className="mt-6">
                <legend className="text-base font-black text-ink dark:text-white">
                  محدوده ارسال
                </legend>
                <p className="mt-2 text-sm leading-7 text-ink/55 dark:text-white/55">
                  برای محاسبه هزینه ارسال، یکی از گزینه‌های زیر را انتخاب کنید.
                </p>
                {shippingRates ? (
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {shippingZoneOrder.map((zone) => {
                      const rate = shippingRates[zone];
                      const isSelected = formData.shipping_zone === zone;

                      return (
                        <label
                          className={
                            isSelected
                              ? "cursor-pointer rounded-2xl border-2 border-coral bg-coral/5 p-4 shadow-sm transition dark:bg-coral/10"
                              : "cursor-pointer rounded-2xl border-2 border-ink/10 bg-cream/70 p-4 transition hover:border-coral/45 dark:border-white/10 dark:bg-slate-950/45 dark:hover:border-coral/60"
                          }
                          key={zone}
                        >
                          <span className="flex items-start gap-3">
                            <input
                              aria-describedby="shipping-zone-error"
                              checked={isSelected}
                              className="mt-1 size-4 shrink-0 accent-coral"
                              name="shipping_zone"
                              onChange={() => updateField("shipping_zone", zone)}
                              required
                              type="radio"
                              value={zone}
                            />
                            <span className="min-w-0 flex-1">
                              <span className="block font-black text-ink dark:text-white">
                                {rate.label}
                              </span>
                              <span className="mt-1 block text-sm font-bold text-coral">
                                {formatToman(rate.fee)}
                              </span>
                              <span className="mt-2 block text-xs text-ink/50 dark:text-white/50">
                                {isSelected ? "انتخاب شده" : "انتخاب این محدوده"}
                              </span>
                            </span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                ) : null}
                {validationErrors.shipping_zone ? (
                  <span
                    className="mt-2 block text-xs font-bold text-rose-600 dark:text-rose-300"
                    id="shipping-zone-error"
                  >
                    {validationErrors.shipping_zone}
                  </span>
                ) : null}
              </fieldset>

              {couponMessage ? (
                <p
                  className={
                    couponTone === "success"
                      ? "mt-5 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
                      : "mt-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700"
                  }
                >
                  {couponMessage}
                </p>
              ) : null}

              <label className="mt-5 block">
                <span className="text-sm font-bold text-ink">
                  آدرس کامل ارسال
                </span>
                <textarea
                  className="mt-2 min-h-36 w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3 text-sm leading-7 outline-none transition placeholder:text-ink/30 focus:border-coral"
                  onChange={(event) =>
                    updateField("shipping_address", event.target.value)
                  }
                  placeholder="استان، شهر، خیابان، پلاک و توضیحات لازم برای ارسال"
                  value={formData.shipping_address}
                />
                {validationErrors.shipping_address ? (
                  <span className="mt-2 block text-xs font-bold text-rose-600">
                    {validationErrors.shipping_address}
                  </span>
                ) : null}
              </label>

              {pageError ? (
                <p className="mt-5 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold leading-7 text-rose-700">
                  {pageError}
                </p>
              ) : null}

              <Button
                className="mt-6 w-full"
                disabled={isSubmitting || !shippingRates}
                type="submit"
                variant="coral"
              >
                {isSubmitting
                  ? "در حال ثبت سفارش..."
                  : "ثبت سفارش و ادامه پرداخت"}
              </Button>
            </form>

            <CheckoutSummary items={items} summary={summary} />
          </>
        )}
      </section>
    </>
  );
}

function LoginRequiredState() {
  return (
    <div className="rounded-[2rem] border border-dashed border-ink/10 bg-white p-8 text-center shadow-sm">
      <span className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-cream text-coral">
        <LogIn className="size-8" aria-hidden="true" />
      </span>
      <h2 className="mt-5 text-2xl font-black text-ink">
        برای تسویه حساب وارد شوید
      </h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-ink/60">
        برای ثبت سفارش و ادامه پرداخت، ابتدا وارد حساب کاربری خود شوید.
      </p>
      <Button asChild className="mt-6" variant="coral">
        <Link href="/login">ورود به حساب کاربری</Link>
      </Button>
    </div>
  );
}

function EmptyCartState() {
  return (
    <div>
      <EmptyState
        description="برای ثبت سفارش، ابتدا محصولی را به سبد خرید اضافه کنید."
        icon={PackageOpen}
        title="سبد خرید شما خالی است"
      />
      <div className="mt-5 text-center">
        <Button asChild variant="coral">
          <Link href="/products">مشاهده محصولات</Link>
        </Button>
      </div>
    </div>
  );
}

function CheckoutSummary({
  items,
  summary,
}: {
  items: CartItem[];
  summary: {
    subtotal: number;
    discount: number;
    shipping: number;
    total: number;
  };
}) {
  return (
    <aside className="h-fit rounded-[2rem] bg-white p-6 shadow-sm lg:sticky lg:top-28">
      <div className="flex items-center gap-2">
        <ShoppingBag className="size-6 text-coral" />
        <h2 className="text-2xl font-black text-ink">خلاصه پرداخت</h2>
      </div>

      <div className="mt-6 space-y-4">
        {items.map((item) => (
          <div
            className="flex items-start justify-between gap-4 rounded-2xl bg-cream px-4 py-3 text-sm"
            key={item.id}
          >
            <div>
              <p className="font-black leading-6 text-ink">
                {item.product.name}
              </p>
              <p className="mt-1 text-xs text-ink/45">
                تعداد: {toPersianDigits(item.quantity)}
              </p>
            </div>
            <span className="whitespace-nowrap text-xs font-black text-ink">
              {formatToman(getCartItemTotal(item))}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-6 space-y-4 text-sm">
        <Summary label="جمع سفارش" value={summary.subtotal} />
        <Summary label="تخفیف" value={-summary.discount} />
        <Summary label="هزینه ارسال" value={summary.shipping} />
      </div>
      <div className="mt-6 border-t border-ink/10 pt-5">
        <Summary large label="مبلغ نهایی" value={summary.total} />
      </div>
    </aside>
  );
}

function Field({
  label,
  error,
  ltr = false,
  ...props
}: {
  label: string;
  error?: string;
  placeholder: string;
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
        {...props}
      />
      {error ? (
        <span className="mt-2 block text-xs font-bold text-rose-600">
          {error}
        </span>
      ) : null}
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
        {formatToman(value)}
      </span>
    </div>
  );
}

function validateCheckoutForm(formData: CheckoutFormData) {
  const errors: ValidationErrors = {};
  const recipientPhone = normalizeDigits(formData.recipient_phone).trim();
  const postalCode = normalizeDigits(formData.postal_code).replace(/\D/g, "");

  if (!formData.recipient_name.trim()) {
    errors.recipient_name = "نام گیرنده الزامی است.";
  }

  if (!recipientPhone) {
    errors.recipient_phone = "شماره موبایل گیرنده الزامی است.";
  } else if (!/^09\d{9}$/.test(recipientPhone)) {
    errors.recipient_phone = "شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد.";
  }

  if (!postalCode) {
    errors.postal_code = "کد پستی الزامی است.";
  } else if (postalCode.length < 10) {
    errors.postal_code = "کد پستی باید حداقل ۱۰ رقم باشد.";
  }

  if (!formData.shipping_address.trim()) {
    errors.shipping_address = "آدرس کامل ارسال الزامی است.";
  }

  if (!formData.shipping_zone) {
    errors.shipping_zone = "انتخاب محدوده ارسال الزامی است.";
  }

  return errors;
}

function normalizeDigits(value: string) {
  const persianDigits = "۰۱۲۳۴۵۶۷۸۹";
  const arabicDigits = "٠١٢٣٤٥٦٧٨٩";

  return value.replace(/[۰-۹٠-٩]/g, (digit) => {
    const persianIndex = persianDigits.indexOf(digit);

    if (persianIndex >= 0) {
      return String(persianIndex);
    }

    return String(arabicDigits.indexOf(digit));
  });
}

function getCartItemTotal(item: CartItem) {
  return (
    item.subtotal ||
    item.line_total ||
    getProductPrice(item.product) * item.quantity
  );
}

function getCartSubtotal(cart: Cart | null) {
  if (!cart) {
    return 0;
  }

  return (
    cart.subtotal ||
    cart.subtotal_amount ||
    cart.total_price ||
    cart.items.reduce((sum, item) => sum + getCartItemTotal(item), 0)
  );
}

function getNumberValue(...values: Array<number | undefined>) {
  return values.find((value) => typeof value === "number") || 0;
}

function buildSummary(
  cart: Cart | null,
  couponPreview: CouponPreviewResponse | null,
  shipping: number,
) {
  const subtotal = getNumberValue(
    couponPreview?.subtotal_amount,
    couponPreview?.subtotal,
    getCartSubtotal(cart),
  );
  const discount = getNumberValue(
    couponPreview?.discount_amount,
    couponPreview?.discount,
  );
  const total = Math.max(0, subtotal - discount + shipping);

  return {
    subtotal,
    discount,
    shipping,
    total,
  };
}

function extractOrderId(response: CheckoutResponse) {
  const order = "order" in response ? response.order : response;
  return order.id;
}
