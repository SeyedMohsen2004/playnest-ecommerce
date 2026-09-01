import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const checkoutSource = await readFile(
  new URL("./page.tsx", import.meta.url),
  "utf8",
);

test("checkout does not disclose development coupon codes", () => {
  assert.doesNotMatch(checkoutSource, /OFF10|GAME50000/u);
  assert.match(checkoutSource, /placeholder="کد تخفیف خود را وارد کنید"/u);
});

test("checkout keeps the existing coupon application action", () => {
  assert.match(checkoutSource, /onClick=\{handleApplyCoupon\}/u);
  assert.match(checkoutSource, /type="button"/u);
});
