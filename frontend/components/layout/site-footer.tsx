import { Facebook, Instagram, Mail, MapPin, Phone } from "lucide-react";
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

export function SiteFooter() {
  return (
    <footer className="border-t border-ink/5 bg-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.35fr_0.8fr_0.9fr_1fr] lg:px-8">
        <div>
          <Link href="/" className="text-2xl font-black tracking-tight text-ink">
            IpakToys
          </Link>
          <p className="mt-4 max-w-md text-sm leading-7 text-ink/65">
            فروشگاه بازی فکری، بردگیم، پازل و محصولات ساختنی برای کودک،
            نوجوان و خانواده؛ با تمرکز بر انتخاب آگاهانه، سرگرمی سالم و تجربه
            خرید مطمئن.
          </p>
          <div className="mt-6 flex gap-3">
            {[Instagram, Facebook, Mail].map((Icon, index) => (
              <span
                className="flex size-10 items-center justify-center rounded-full bg-cream text-ink"
                key={index}
              >
                <Icon className="size-4" aria-hidden="true" />
              </span>
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

          <div className="mt-6 rounded-3xl border border-dashed border-ink/15 bg-cream p-4 text-center">
            <p className="text-sm font-black text-ink">
              محل نمایش نماد اعتماد الکترونیکی
            </p>
            <p className="mt-2 text-xs leading-6 text-ink/50">
              این بخش تا زمان دریافت نماد اعتماد توسط مالک کسب‌وکار، فقط
              placeholder است.
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-ink/5 px-4 py-5 text-center text-xs text-ink/50">
        © ۲۰۲۶ IpakToys Ecommerce. تمامی حقوق محفوظ است.
      </div>
    </footer>
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
