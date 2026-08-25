type ApiErrorLike = Error & {
  status: number;
  data: unknown;
};

type ErrorEntry = {
  field?: string;
  message: string;
};

const FIELD_LABELS: Record<string, string> = {
  address: "آدرس",
  cart: "سبد خرید",
  code: "کد تأیید",
  coupon: "کد تخفیف",
  coupon_code: "کد تخفیف",
  email: "ایمیل",
  first_name: "نام",
  last_name: "نام خانوادگی",
  password: "رمز عبور",
  password_confirm: "تکرار رمز عبور",
  phone_number: "شماره موبایل",
  postal_code: "کد پستی",
  quantity: "تعداد",
  recipient_name: "نام گیرنده",
  recipient_phone: "شماره موبایل گیرنده",
  shipping_address: "آدرس ارسال",
  shipping_zone: "محدوده ارسال",
};

const GENERIC_ERROR =
  "انجام درخواست با مشکل روبه‌رو شد. لطفاً دوباره تلاش کنید.";
const NETWORK_ERROR =
  "ارتباط با سرور برقرار نشد. لطفاً دوباره تلاش کنید.";
const SERVER_ERROR =
  "مشکلی در سرور پیش آمد. لطفاً کمی بعد دوباره تلاش کنید.";

function isApiError(error: unknown): error is ApiErrorLike {
  return (
    error instanceof Error &&
    typeof (error as Partial<ApiErrorLike>).status === "number" &&
    "data" in error
  );
}

function collectErrorEntries(
  value: unknown,
  field?: string,
): ErrorEntry[] {
  if (!value) {
    return [];
  }

  if (typeof value === "string") {
    return [{ field, message: value }];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => collectErrorEntries(item, field));
  }

  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(
      ([key, item]) =>
        collectErrorEntries(
          item,
          ["detail", "message", "non_field_errors"].includes(key)
            ? undefined
            : key,
        ),
    );
  }

  return [];
}

function containsPersian(value: string) {
  return /[\u0600-\u06ff]/u.test(value);
}

function containsSensitiveTechnicalContent(value: string) {
  return /(?:traceback|exception|stack trace|sql|database|merchant|authority|token|secret|api[_ -]?key|\/var\/|\/home\/|[a-z]:\\)/iu.test(
    value,
  );
}

function fieldLabel(field?: string) {
  return field ? FIELD_LABELS[field] : undefined;
}

function requiredMessage(field?: string) {
  const label = fieldLabel(field);
  return label
    ? `لطفاً ${label} را وارد کنید.`
    : "لطفاً اطلاعات ضروری را کامل کنید.";
}

function invalidFieldMessage(field?: string) {
  const label = fieldLabel(field);
  return label
    ? `${label} واردشده معتبر نیست.`
    : "اطلاعات واردشده معتبر نیست.";
}

function localizeMessage(entry: ErrorEntry): string | null {
  const message = entry.message.replace(/\s+/g, " ").trim();
  const normalized = message.toLowerCase();
  const label = fieldLabel(entry.field);

  if (
    !message ||
    message.length > 300 ||
    containsSensitiveTechnicalContent(message)
  ) {
    return null;
  }

  if (
    normalized.includes("invalid phone number or password") ||
    normalized.includes("invalid credentials")
  ) {
    return "شماره موبایل یا رمز عبور اشتباه است.";
  }

  if (
    normalized.includes("authentication credentials were not provided") ||
    normalized.includes("authentication session is unavailable") ||
    normalized.includes("token is invalid or expired") ||
    normalized.includes("user is not eligible for authentication")
  ) {
    return "برای انجام این کار ابتدا وارد حساب کاربری شوید.";
  }

  if (
    normalized.includes("permission denied") ||
    normalized.includes("do not have permission") ||
    normalized.includes("not allowed")
  ) {
    return "اجازه انجام این کار را ندارید.";
  }

  if (
    normalized.includes("request was throttled") ||
    normalized.includes("too many requests") ||
    normalized.includes("too many login attempts")
  ) {
    return "تعداد تلاش‌ها بیش از حد مجاز است. لطفاً کمی بعد دوباره تلاش کنید.";
  }

  if (
    normalized === "this field is required." ||
    normalized === "this field may not be blank." ||
    normalized === "this field may not be null."
  ) {
    return requiredMessage(entry.field);
  }

  if (
    normalized.includes("valid iranian mobile") ||
    normalized.includes("phone number must") ||
    (entry.field === "phone_number" && normalized.includes("11 characters"))
  ) {
    return "شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.";
  }

  if (
    normalized.includes("already uses this phone number") ||
    normalized.includes("phone number already exists") ||
    normalized.includes("user with this phone number already exists")
  ) {
    return "این شماره موبایل قبلاً ثبت شده است. لطفاً وارد حساب خود شوید.";
  }

  if (normalized.includes("passwords do not match")) {
    return "رمز عبور و تکرار آن یکسان نیستند.";
  }

  if (
    normalized.includes("password is too short") ||
    (entry.field === "password" && normalized.includes("at least"))
  ) {
    return "رمز عبور باید حداقل ۸ نویسه باشد.";
  }

  if (normalized.includes("password is too common")) {
    return "این رمز عبور بیش از حد رایج است. رمز دیگری انتخاب کنید.";
  }

  if (normalized.includes("password is too similar")) {
    return "رمز عبور بیش از حد شبیه اطلاعات شخصی شماست.";
  }

  if (normalized.includes("password is entirely numeric")) {
    return "رمز عبور نمی‌تواند فقط از عدد تشکیل شود.";
  }

  if (
    normalized.includes("valid email address") ||
    (entry.field === "email" && normalized.includes("valid"))
  ) {
    return "ایمیل واردشده معتبر نیست.";
  }

  if (normalized.includes("cart is empty")) {
    return "سبد خرید شما خالی است.";
  }

  if (normalized.includes("cart changed during checkout")) {
    return "سبد خرید در زمان ثبت سفارش تغییر کرده است. لطفاً آن را دوباره بررسی کنید.";
  }

  if (
    normalized.includes("quantity cannot exceed available stock") ||
    normalized.includes("insufficient stock") ||
    normalized.includes("available stock")
  ) {
    return "موجودی این کالا برای تعداد انتخاب‌شده کافی نیست.";
  }

  if (
    normalized.includes("product is inactive") ||
    normalized.includes("inactive products")
  ) {
    return "این کالا در حال حاضر قابل سفارش نیست.";
  }

  if (
    normalized.includes("coupon was not found") ||
    normalized.includes("coupon is inactive") ||
    normalized.includes("coupon is not active yet") ||
    normalized.includes("coupon has expired") ||
    normalized.includes("coupon usage limit") ||
    normalized.includes("minimum order")
  ) {
    return "کد تخفیف معتبر نیست یا شرایط استفاده از آن فراهم نشده است.";
  }

  if (normalized.includes("select a valid shipping zone")) {
    return "لطفاً محدوده ارسال معتبری انتخاب کنید.";
  }

  if (normalized.includes("order was not found")) {
    return "سفارش موردنظر پیدا نشد.";
  }

  if (
    normalized.includes("gateway") ||
    normalized.includes("payment authority") ||
    normalized.includes("payment url") ||
    normalized.includes("only pending payments")
  ) {
    return "آماده‌سازی پرداخت انجام نشد. لطفاً دوباره تلاش کنید.";
  }

  if (normalized.includes("already reviewed this product")) {
    return "شما قبلاً برای این محصول نظر ثبت کرده‌اید.";
  }

  if (containsPersian(message)) {
    return label && !message.includes(label) ? `${label}: ${message}` : message;
  }

  if (
    normalized.includes("invalid") ||
    normalized.includes("not a valid choice") ||
    normalized.includes("ensure this field")
  ) {
    return invalidFieldMessage(entry.field);
  }

  return null;
}

export function getFriendlyApiError(
  error: unknown,
  fallbackMessage = GENERIC_ERROR,
) {
  if (error instanceof TypeError) {
    return NETWORK_ERROR;
  }

  if (isApiError(error)) {
    if (error.status >= 500) {
      return SERVER_ERROR;
    }
    if (error.status === 401) {
      return "برای انجام این کار ابتدا وارد حساب کاربری شوید.";
    }
    if (error.status === 403) {
      return "اجازه انجام این کار را ندارید.";
    }
    if (error.status === 404) {
      return "اطلاعات موردنظر پیدا نشد.";
    }
    if (error.status === 429) {
      return "تعداد تلاش‌ها بیش از حد مجاز است. لطفاً کمی بعد دوباره تلاش کنید.";
    }

    const messages = collectErrorEntries(error.data)
      .map(localizeMessage)
      .filter((message): message is string => Boolean(message));

    return [...new Set(messages)].slice(0, 3).join(" ") || fallbackMessage;
  }

  const messages = collectErrorEntries(error)
    .map(localizeMessage)
    .filter((message): message is string => Boolean(message));

  return [...new Set(messages)].slice(0, 3).join(" ") || fallbackMessage;
}

function formatStockMessage(availableStock?: number | null) {
  if (typeof availableStock === "number" && availableStock >= 0) {
    const persianStock = String(availableStock).replace(/\d/g, (digit) =>
      "۰۱۲۳۴۵۶۷۸۹".charAt(Number(digit)),
    );
    return `موجودی این کالا فقط ${persianStock} عدد است. لطفاً تعداد کمتری انتخاب کنید.`;
  }

  return "موجودی این کالا کافی نیست. لطفاً تعداد کمتری انتخاب کنید.";
}

export function getCartErrorMessage(
  error: unknown,
  fallbackMessage = "افزودن کالا به سبد خرید انجام نشد. لطفاً دوباره تلاش کنید.",
  availableStock?: number | null,
) {
  const rawValue = isApiError(error) ? error.data : error;
  const combinedMessage = collectErrorEntries(rawValue)
    .map(({ message }) => message.trim().toLowerCase())
    .join(" ");

  if (
    combinedMessage.includes("quantity cannot exceed available stock") ||
    combinedMessage.includes("insufficient stock") ||
    combinedMessage.includes("available stock") ||
    combinedMessage.includes("stock") ||
    combinedMessage.includes("inventory") ||
    combinedMessage.includes("موجودی")
  ) {
    return formatStockMessage(availableStock);
  }

  if (
    combinedMessage.includes("quantity") ||
    combinedMessage.includes("تعداد") ||
    combinedMessage.includes("greater than or equal to") ||
    combinedMessage.includes("min_value")
  ) {
    return "تعداد انتخاب‌شده معتبر نیست.";
  }

  if (
    combinedMessage.includes("inactive") ||
    combinedMessage.includes("not active") ||
    combinedMessage.includes("ناموجود")
  ) {
    return "این کالا در حال حاضر ناموجود است.";
  }

  return getFriendlyApiError(error, fallbackMessage);
}

export function getStockLimitMessage(availableStock: number) {
  return formatStockMessage(availableStock);
}
