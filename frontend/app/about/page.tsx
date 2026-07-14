import type { Metadata } from "next";

import {
  DraftNotice,
  InfoSection,
  LegalPageLayout,
} from "@/components/shared/legal-page-layout";
import { absoluteUrl, SITE_NAME } from "@/lib/seo";

export const metadata: Metadata = {
  title: {
    absolute: "درباره ایپک تویز | IpakToys",
  },
  description:
    "درباره فروشگاه ایپک تویز، عرضه‌کننده بازی فکری، بردگیم، پازل، لگو و محصولات سرگرمی خانوادگی.",
  alternates: {
    canonical: absoluteUrl("/about"),
  },
  openGraph: {
    title: "درباره ایپک تویز | IpakToys",
    description:
      "معرفی فروشگاه ایپک تویز و تمرکز آن روی بازی فکری، بردگیم، پازل و سرگرمی‌های خانوادگی.",
    url: absoluteUrl("/about"),
    siteName: SITE_NAME,
    locale: "fa_IR",
    type: "website",
  },
};

export default function AboutPage() {
  return (
    <LegalPageLayout
      title="درباره IpakToys"
      description="IpakToys فروشگاه بازی فکری، بردگیم، پازل و محصولات ساختنی است که با هدف ساده‌تر کردن انتخاب محصولات سرگرمی و آموزشی برای کودک، نوجوان و خانواده فعالیت می‌کند."
    >
      <InfoSection title="معرفی فروشگاه IpakToys">
        IpakToys با تمرکز بر بازی‌های فکری، بردگیم‌ها، پازل‌ها و محصولات
        ساختنی شکل گرفته است. هدف فروشگاه این است که خانواده‌ها، نوجوانان و
        علاقه‌مندان بازی‌های رومیزی بتوانند محصول مناسب سن، سلیقه و نوع
        دورهمی خود را شفاف‌تر انتخاب کنند.
      </InfoSection>

      <InfoSection title="تمرکز ما">
        تمرکز IpakToys روی محصولاتی است که علاوه بر سرگرمی، به تقویت خلاقیت،
        تمرکز، حل مسئله، تعامل خانوادگی و تجربه بازی گروهی کمک می‌کنند. در
        معرفی محصولات تلاش می‌شود اطلاعاتی مانند سبک بازی، رده سنی، موجودی و
        ویژگی‌های اصلی کالا به‌صورت روشن نمایش داده شود.
      </InfoSection>

      <InfoSection title="انتخاب محصول مناسب">
        انتخاب بردگیم، بازی فکری یا پازل مناسب به سن، تعداد بازیکنان، زمان بازی
        و سطح پیچیدگی محصول بستگی دارد. اطلاعات نهایی هر کالا باید بر اساس
        مشخصات تامین‌کننده یا مالک فروشگاه تکمیل و تایید شود.
      </InfoSection>

      <InfoSection title="اطلاعات فروشگاه">
        <ul className="space-y-2">
          <li>شماره تماس: 09145863568</li>
          <li>ایمیل: Ipacktoys@yahoo.com</li>
          <li>آدرس: تبریز - بازار مشروطه، حیاط پایین، پلاک C1</li>
        </ul>
      </InfoSection>

      <DraftNotice />
    </LegalPageLayout>
  );
}
