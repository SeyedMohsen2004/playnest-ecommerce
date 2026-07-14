import type { Metadata } from "next";

import {
  DraftNotice,
  InfoSection,
  LegalPageLayout,
} from "@/components/shared/legal-page-layout";
import { absoluteUrl, SITE_NAME } from "@/lib/seo";

export const metadata: Metadata = {
  title: {
    absolute: "تماس با ایپک تویز | IpakToys",
  },
  description:
    "راه‌های تماس با فروشگاه ایپک تویز برای خرید بازی فکری، بردگیم، پازل، لگو و محصولات سرگرمی.",
  alternates: {
    canonical: absoluteUrl("/contact"),
  },
  openGraph: {
    title: "تماس با ایپک تویز | IpakToys",
    description:
      "اطلاعات تماس، آدرس و راه ارتباطی فروشگاه ایپک تویز در تبریز.",
    url: absoluteUrl("/contact"),
    siteName: SITE_NAME,
    locale: "fa_IR",
    type: "website",
  },
};

export default function ContactPage() {
  return (
    <LegalPageLayout
      title="تماس با ما"
      description="برای دریافت راهنمایی درباره خرید بازی‌های فکری، بردگیم‌ها، سفارش‌ها و همکاری با IpakToys می‌توانید از راه‌های ارتباطی زیر استفاده کنید."
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_0.85fr]">
        <form className="rounded-[2rem] border border-ink/5 bg-cream/60 p-5 sm:p-6">
          <h2 className="text-xl font-black text-ink">فرم تماس نمایشی</h2>
          <p className="mt-2 text-sm leading-7 text-ink/55">
            این فرم فعلا نمایشی است و پس از اتصال سرویس تماس، پیام‌ها ارسال
            خواهند شد.
          </p>
          <div className="mt-5 space-y-4">
            <Field label="نام و نام خانوادگی" placeholder="نام شما" />
            <Field label="شماره تماس یا ایمیل" placeholder="09145863568" ltr />
            <label className="block">
              <span className="text-sm font-bold text-ink">پیام</span>
              <textarea
                className="mt-2 min-h-36 w-full rounded-2xl border border-ink/10 bg-white px-4 py-3 text-sm leading-7 outline-none transition placeholder:text-ink/30 focus:border-coral"
                placeholder="متن پیام خود را بنویسید"
              />
            </label>
            <button
              className="w-full rounded-full bg-coral px-5 py-3 text-sm font-bold text-white shadow-soft"
              type="button"
            >
              ارسال پیام
            </button>
          </div>
        </form>

        <InfoSection title="اطلاعات تماس">
          <ul className="space-y-3">
            <li>شماره تماس: 09145863568</li>
            <li>ایمیل: Ipacktoys@yahoo.com</li>
            <li>آدرس: تبریز - بازار مشروطه، حیاط پایین، پلاک C1</li>
            <li>ساعات پاسخگویی: شنبه تا پنجشنبه، ۹ تا ۱۸</li>
          </ul>
          <p className="mt-5 rounded-2xl bg-white px-4 py-3 text-xs leading-6 text-ink/55">
            اطلاعات تماس بالا برای IpakToys ثبت شده است و در محیط تولید باید
            توسط مالک فروشگاه نهایی و تایید شود.
          </p>
        </InfoSection>
      </div>

      <DraftNotice />
    </LegalPageLayout>
  );
}

function Field({
  label,
  placeholder,
  ltr = false,
}: {
  label: string;
  placeholder: string;
  ltr?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-ink">{label}</span>
      <input
        className="mt-2 h-12 w-full rounded-2xl border border-ink/10 bg-white px-4 text-sm outline-none transition placeholder:text-ink/30 focus:border-coral"
        dir={ltr ? "ltr" : "rtl"}
        placeholder={placeholder}
      />
    </label>
  );
}
