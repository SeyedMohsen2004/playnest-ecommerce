export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://ipaktoys.ir"
).replace(/\/+$/, "");

export const SITE_NAME = "ایپک تویز";

export const DEFAULT_TITLE =
  "ایپک تویز | فروشگاه اسباب‌بازی، بازی فکری و بردگیم";

export const DEFAULT_DESCRIPTION =
  "خرید اسباب‌بازی، بازی فکری، بردگیم، پازل، لگو و سرگرمی‌های خانوادگی از فروشگاه ایپک تویز.";

export const SEO_KEYWORDS = [
  "ایپک تویز",
  "ipak toys",
  "IpakToys",
  "فروشگاه ایپک تویز",
  "خرید اسباب بازی",
  "فروشگاه اسباب بازی",
  "بازی فکری",
  "بردگیم",
  "پازل",
  "لگو",
  "اسباب بازی تبریز",
  "فروشگاه اسباب بازی در تبریز",
];

export function absoluteUrl(path = "/") {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${SITE_URL}${normalizedPath}`;
}

export function truncateMetaDescription(value: string, maxLength = 155) {
  const cleaned = value.replace(/\s+/g, " ").trim();

  if (cleaned.length <= maxLength) {
    return cleaned;
  }

  return `${cleaned.slice(0, maxLength - 1).trim()}…`;
}
