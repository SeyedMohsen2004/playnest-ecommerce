import { Facebook, Instagram, Mail, MapPin, Phone } from "lucide-react";
import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-ink/5 bg-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
        <div>
          <Link href="/" className="text-2xl font-black tracking-tight text-ink">
            PlayNest
          </Link>
          <p className="mt-4 max-w-md text-sm leading-7 text-ink/65">
            تجربه‌ای شاد و مطمئن برای خرید اسباب‌بازی؛ با محصولات ایمن، طراحی
            مدرن و مسیر خریدی ساده برای خانواده‌ها.
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

        <div>
          <h3 className="font-bold text-ink">خرید</h3>
          <ul className="mt-4 space-y-3 text-sm text-ink/65">
            <li>لگو و ساختنی</li>
            <li>عروسک</li>
            <li>اسباب‌بازی آموزشی</li>
            <li>نوزاد و خردسال</li>
          </ul>
        </div>

        <div>
          <h3 className="font-bold text-ink">ارتباط با ما</h3>
          <ul className="mt-4 space-y-3 text-sm text-ink/65">
            <li className="flex items-center gap-2">
              <Phone className="size-4" /> ۰۲۱-۰۰۰۰-۰۰۰۰
            </li>
            <li className="flex items-center gap-2">
              <Mail className="size-4" /> hello@playnest.local
            </li>
            <li className="flex items-center gap-2">
              <MapPin className="size-4" /> فروشگاه آنلاین اسباب‌بازی
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-ink/5 px-4 py-5 text-center text-xs text-ink/50">
        © ۲۰۲۶ PlayNest Ecommerce. تمامی حقوق محفوظ است.
      </div>
    </footer>
  );
}
