import { APIError } from "@/lib/api/client";
import { toPersianDigits } from "@/lib/format";

function collectErrorMessages(value: unknown): string[] {
  if (!value) {
    return [];
  }

  if (typeof value === "string") {
    return [value];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => collectErrorMessages(item));
  }

  if (typeof value === "object") {
    return Object.values(value).flatMap((item) => collectErrorMessages(item));
  }

  return [];
}

function formatStockMessage(availableStock?: number | null) {
  if (typeof availableStock === "number" && availableStock >= 0) {
    return `موجودی این کالا فقط ${toPersianDigits(availableStock)} عدد است. لطفاً تعداد کمتری انتخاب کنید.`;
  }

  return "موجودی این کالا کافی نیست. لطفاً تعداد کمتری انتخاب کنید.";
}

export function getCartErrorMessage(
  error: unknown,
  fallbackMessage = "افزودن کالا به سبد خرید انجام نشد. لطفاً دوباره تلاش کنید.",
  availableStock?: number | null,
) {
  const messages =
    error instanceof APIError
      ? collectErrorMessages(error.data).concat(error.message)
      : error instanceof Error
        ? [error.message]
        : collectErrorMessages(error);

  const normalizedMessages = messages
    .map((message) => message.trim())
    .filter(Boolean);
  const combinedMessage = normalizedMessages.join(" ").toLowerCase();

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

  const userFacingMessage = normalizedMessages.find(
    (message) => message.length <= 180 && !message.includes("{"),
  );

  return userFacingMessage || fallbackMessage;
}

export function getStockLimitMessage(availableStock: number) {
  return formatStockMessage(availableStock);
}
