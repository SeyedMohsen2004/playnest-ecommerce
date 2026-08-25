import assert from "node:assert/strict";
import test from "node:test";

import {
  getCartErrorMessage,
  getFriendlyApiError,
} from "./errors.ts";

function apiError(status, data, message = "Internal API client detail") {
  const error = new Error(message);
  error.status = status;
  error.data = data;
  return error;
}

test("normalizes generic and field DRF errors into Persian", () => {
  assert.equal(
    getFriendlyApiError(
      apiError(400, { detail: "Invalid phone number or password." }),
    ),
    "شماره موبایل یا رمز عبور اشتباه است.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(400, { phone_number: ["This field is required."] }),
    ),
    "لطفاً شماره موبایل را وارد کنید.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(400, { non_field_errors: ["Passwords do not match."] }),
    ),
    "رمز عبور و تکرار آن یکسان نیستند.",
  );
});

test("localizes registration validation without exposing raw English", () => {
  assert.equal(
    getFriendlyApiError(
      apiError(400, {
        phone_number: [
          "Enter a valid Iranian mobile number starting with 09.",
        ],
      }),
    ),
    "شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(400, {
        phone_number: ["An account already uses this phone number."],
      }),
    ),
    "این شماره موبایل قبلاً ثبت شده است. لطفاً وارد حساب خود شوید.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(400, {
        password: [
          "This password is too common.",
          "This password is entirely numeric.",
        ],
      }),
    ),
    "این رمز عبور بیش از حد رایج است. رمز دیگری انتخاب کنید. رمز عبور نمی‌تواند فقط از عدد تشکیل شود.",
  );
});

test("uses safe network, server, and unknown fallbacks", () => {
  assert.equal(
    getFriendlyApiError(new TypeError("Failed to fetch")),
    "ارتباط با سرور برقرار نشد. لطفاً دوباره تلاش کنید.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(500, { detail: "SQL exception at /var/private/app.py" }),
    ),
    "مشکلی در سرور پیش آمد. لطفاً کمی بعد دوباره تلاش کنید.",
  );
  assert.equal(
    getFriendlyApiError(
      new Error("Authentication backend leaked an internal exception"),
      "خطای امن",
    ),
    "خطای امن",
  );
});

test("normalizes authorization and commerce validation safely", () => {
  assert.equal(
    getFriendlyApiError(apiError(401, { detail: "Token details" })),
    "برای انجام این کار ابتدا وارد حساب کاربری شوید.",
  );
  assert.equal(
    getFriendlyApiError(apiError(403, { detail: "Private ownership reason" })),
    "اجازه انجام این کار را ندارید.",
  );
  assert.equal(
    getFriendlyApiError(
      apiError(400, { coupon: ["Coupon has expired."] }),
    ),
    "کد تخفیف معتبر نیست یا شرایط استفاده از آن فراهم نشده است.",
  );
  assert.equal(
    getCartErrorMessage(
      apiError(400, { quantity: ["Insufficient stock."] }),
      undefined,
      2,
    ),
    "موجودی این کالا فقط ۲ عدد است. لطفاً تعداد کمتری انتخاب کنید.",
  );
});
