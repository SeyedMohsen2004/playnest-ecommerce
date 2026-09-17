import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

// Exercise the actual TSX component using the existing compiler, no test SDK.
const source = readFileSync(new URL("./components/orders/postal-tracking.tsx", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
});
const componentModule = { exports: {} };
new Function("require", "module", "exports", outputText)(
  createRequire(import.meta.url), componentModule, componentModule.exports,
);
const { PostalTracking } = componentModule.exports;
const render = (status, postal_tracking_code) => renderToStaticMarkup(
  React.createElement(PostalTracking, { order: { status, postal_tracking_code } }),
);

for (const status of ["shipped", "delivered"]) {
  test(`${status} renders a Persian label and LTR tracking text`, () => {
    const html = render(status, "123456789012345678901234");
    assert.match(html, /کد رهگیری پستی/u);
    assert.match(html, /dir="rtl"/u);
    assert.match(html, /dir="ltr"/u);
    assert.match(html, /overflow-wrap:anywhere/u);
    assert.match(html, /123456789012345678901234/u);
  });
}
for (const status of ["pending", "payment_failed", "paid", "processing", "cancelled"]) {
  test(`${status} hides tracking even if supplied`, () => {
    assert.equal(render(status, "PRIVATE"), "");
  });
}
test("no empty tracking card for missing or blank values", () => {
  for (const code of [undefined, null, "", "   "]) {
    assert.equal(render("shipped", code), "");
  }
});
test("tracking is escaped as text, never HTML", () => {
  const html = render("shipped", '<img src=x onerror="alert(1)">');
  assert.doesNotMatch(html, /<img/u);
  assert.match(html, /&lt;img/u);
});
