export const SITE_URL = "https://ipaktoys.ir";

export const SITE_NAME = "ایپک تویز";

export const BRAND_NAME_EN = "IpakToys";

export const HOME_TITLE =
  "ایپک تویز | IpakToys | فروشگاه اسباب‌بازی، بازی فکری و بردگیم";

export const HOME_OG_TITLE = "ایپک تویز | IpakToys";

export const HOME_DESCRIPTION =
  "ایپک تویز فروشگاه اسباب‌بازی، بازی فکری، بردگیم، پازل، لگو و سرگرمی‌های خانوادگی است. خرید آنلاین محصولات سرگرمی و اسباب‌بازی از IpakToys.";

export const SEO_KEYWORDS = [
  "ایپک تویز",
  "IpakToys",
  "ipak toys",
  "فروشگاه ایپک تویز",
  "اسباب بازی ایپک تویز",
  "خرید اسباب بازی",
  "فروشگاه اسباب بازی",
  "بازی فکری",
  "بردگیم",
  "پازل",
  "لگو",
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
