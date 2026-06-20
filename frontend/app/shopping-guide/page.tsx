import {
  DraftNotice,
  InfoSection,
  LegalPageLayout,
} from "@/components/shared/legal-page-layout";

const steps = [
  {
    title: "انتخاب محصول",
    description:
      "از صفحه محصولات، اسباب‌بازی‌ها را بر اساس دسته‌بندی، برند، رده سنی یا جستجو بررسی کنید و وارد صفحه جزئیات محصول شوید.",
  },
  {
    title: "افزودن به سبد خرید",
    description:
      "پس از انتخاب محصول، تعداد مورد نظر را مشخص کرده و محصول را به سبد خرید اضافه کنید.",
  },
  {
    title: "ثبت‌نام یا ورود",
    description:
      "برای ثبت سفارش، با شماره موبایل وارد حساب کاربری شوید یا حساب جدید بسازید و کد تایید را وارد کنید.",
  },
  {
    title: "تکمیل اطلاعات ارسال",
    description:
      "نام گیرنده، شماره موبایل، کد پستی و آدرس کامل ارسال را با دقت وارد کنید.",
  },
  {
    title: "پرداخت",
    description:
      "پس از ثبت سفارش، به صفحه پرداخت هدایت می‌شوید. در نسخه توسعه، پرداخت آزمایشی برای تست فرایند فعال است.",
  },
  {
    title: "پیگیری سفارش",
    description:
      "پس از تکمیل سفارش، وضعیت آن از بخش سفارش‌های حساب کاربری قابل مشاهده و پیگیری خواهد بود.",
  },
];

export default function ShoppingGuidePage() {
  return (
    <LegalPageLayout
      title="راهنمای خرید"
      description="برای خرید از PlayNest کافی است چند مرحله ساده را طی کنید."
    >
      <div className="grid gap-5 md:grid-cols-2">
        {steps.map((step, index) => (
          <InfoSection
            key={step.title}
            title={`${new Intl.NumberFormat("fa-IR").format(index + 1)}. ${
              step.title
            }`}
          >
            {step.description}
          </InfoSection>
        ))}
      </div>

      <DraftNotice />
    </LegalPageLayout>
  );
}
