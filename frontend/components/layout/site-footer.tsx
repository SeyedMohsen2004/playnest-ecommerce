import { ExternalLink, Instagram, Mail, MapPin, Phone, Youtube } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const shoppingLinks = [
  { label: "همه محصولات", href: "/products" },
  { label: "دسته‌بندی‌ها", href: "/products#filters" },
  { label: "پیشنهادها", href: "/#offers" },
  { label: "راهنمای خرید", href: "/shopping-guide" },
];

const businessLinks = [
  { label: "درباره ما", href: "/about" },
  { label: "تماس با ما", href: "/contact" },
  { label: "قوانین و مقررات", href: "/terms" },
  { label: "حریم خصوصی", href: "/privacy" },
  { label: "شرایط بازگشت کالا", href: "/returns" },
  { label: "روش‌های ارسال", href: "/shipping" },
];

const storeMapUrl = "https://maps.app.goo.gl/ZVbKKmHzD9DXgtte9";
const enamadTrustSealUrl =
  "https://trustseal.enamad.ir/?id=753502&Code=H2KOQpYuirurt11s3WHVNxggvUSxRg6u";
const enamadLogoUrl =
  "https://trustseal.enamad.ir/logo.aspx?id=753502&Code=H2KOQpYuirurt11s3WHVNxggvUSxRg6u";
const enamadCode = "H2KOQpYuirurt11s3WHVNxggvUSxRg6u";
const enamadCodeAttribute = { code: enamadCode };

const socialLinks = [
  // TODO: Replace placeholder URLs with official IpakToys social profiles.
  { label: "Instagram", href: "#", icon: Instagram },
  { label: "TikTok", href: "#", icon: TikTokIcon },
  { label: "YouTube", href: "#", icon: Youtube },
];

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden border-t border-white/70 bg-gradient-to-br from-white via-cream to-skysoft/70">
      <div className="pointer-events-none absolute -right-20 top-10 size-56 rounded-full bg-coral/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-10 left-0 size-48 rounded-full bg-mint/20 blur-3xl" />
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.35fr_0.8fr_0.9fr_1fr] lg:px-8">
        <div>
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="relative block size-12 overflow-hidden rounded-2xl shadow-card">
              <Image
                alt="لوگوی ایپک تویز"
                className="object-contain"
                fill
                sizes="48px"
                src="/images/brand/ipacktoys-logo.png"
              />
            </span>
            <span className="text-2xl font-black tracking-tight text-ink">
              IpakToys
            </span>
          </Link>
          <p className="mt-4 max-w-md text-sm leading-7 text-ink/65">
            فروشگاه بازی فکری، بردگیم، پازل و محصولات ساختنی برای کودک،
            نوجوان و خانواده؛ با تمرکز بر انتخاب آگاهانه، سرگرمی سالم و تجربه
            خرید مطمئن.
          </p>
          <div className="mt-6 flex gap-3">
            {socialLinks.map(({ label, href, icon: Icon }) => (
              <Link
                aria-label={label}
                className="flex size-10 items-center justify-center rounded-2xl bg-white/85 text-ink shadow-sm ring-1 ring-ink/5 transition hover:-translate-y-0.5 hover:text-coral dark:bg-white/10 dark:ring-white/10 dark:hover:text-sunshine"
                href={href}
                key={label}
              >
                <Icon className="size-4" aria-hidden="true" />
              </Link>
            ))}
          </div>
        </div>

        <FooterColumn title="خرید" links={shoppingLinks} />
        <FooterColumn title="اطلاعات فروشگاه" links={businessLinks} />

        <div>
          <h3 className="font-bold text-ink">ارتباط با ما</h3>
          <ul className="mt-4 space-y-3 text-sm text-ink/65">
            <li className="flex items-center gap-2">
              <Phone className="size-4" /> 09145863568
            </li>
            <li className="flex items-center gap-2">
              <Mail className="size-4" /> Ipacktoys@yahoo.com
            </li>
            <li className="flex items-start gap-2 leading-7">
              <MapPin className="mt-1 size-4" /> تبریز - بازار مشروطه، حیاط
              پایین، پلاک C1
            </li>
          </ul>

          <div className="mt-6 rounded-3xl border border-white/70 bg-white/78 p-4 shadow-sm backdrop-blur dark:border-white/10 dark:bg-white/10">
            <div className="flex items-start gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-coral/12 text-coral dark:bg-white/10 dark:text-sunshine">
                <MapPin className="size-5" aria-hidden="true" />
              </span>
              <div>
                <p className="text-sm font-black text-ink">موقعیت فروشگاه</p>
                <p className="mt-2 text-xs leading-6 text-ink/60">
                  برای مشاهده موقعیت فروشگاه روی نقشه، از لینک زیر استفاده
                  کنید.
                </p>
                <Link
                  className="mt-3 inline-flex items-center gap-2 rounded-2xl bg-gradient-to-l from-coral to-candy px-4 py-2 text-xs font-black text-white shadow-sm transition hover:-translate-y-0.5 hover:text-white"
                  href={storeMapUrl}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  مشاهده روی نقشه
                  <ExternalLink className="size-3.5" aria-hidden="true" />
                </Link>
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-3xl border border-white/70 bg-white/78 p-4 shadow-sm backdrop-blur dark:border-white/10 dark:bg-white/10">
            <p className="text-sm font-black text-ink">اعتماد و مجوزها</p>
            <a
              className="mt-4 inline-flex w-fit max-w-32 items-center justify-center rounded-2xl border border-ink/10 bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-card focus:outline-none focus:ring-2 focus:ring-coral/40 dark:border-white/10 dark:bg-white/90"
              href={enamadTrustSealUrl}
              referrerPolicy="origin"
              rel="noopener noreferrer"
              target="_blank"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                {...enamadCodeAttribute}
                alt="نماد اعتماد الکترونیکی IpakToys"
                className="h-auto w-[104px] cursor-pointer"
                loading="lazy"
                referrerPolicy="origin"
                src={enamadLogoUrl}
              />
            </a>
          </div>
        </div>
      </div>
      <div className="border-t border-ink/5 px-4 py-5 text-center text-xs text-ink/50">
        © ۲۰۲۶ IpakToys Ecommerce. تمامی حقوق محفوظ است.
      </div>
    </footer>
  );
}

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
    >
      <path
        d="M14.75 3v10.2a4.75 4.75 0 1 1-4.75-4.75c.36 0 .7.04 1.03.11v2.88A1.94 1.94 0 1 0 12.1 13.2V3h2.65Zm0 0c.2 1.23.78 2.29 1.75 3.18A6.36 6.36 0 0 0 20 7.75v2.9a8.66 8.66 0 0 1-5.25-2.02V3Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { label: string; href: string }[];
}) {
  return (
    <div>
      <h3 className="font-bold text-ink">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm text-ink/65">
        {links.map((link) => (
          <li key={link.href}>
            <Link className="transition hover:text-coral" href={link.href}>
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
