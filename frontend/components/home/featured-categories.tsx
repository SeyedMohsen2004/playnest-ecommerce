import { CategoryCard } from "@/components/home/category-card";
import { categories } from "@/lib/mock-data";

export function FeaturedCategories() {
  return (
    <section
      className="mx-auto max-w-7xl px-4 py-9 sm:px-6 sm:py-10 lg:px-8"
      id="categories"
    >
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-coral sm:text-sm">
            دسته‌بندی‌های محبوب
          </p>
          <h2 className="mt-2 max-w-3xl text-2xl font-black leading-9 tracking-tight text-ink sm:text-3xl sm:leading-10">
            بازی مناسب جمع و سن موردنظر را سریع‌تر پیدا کنید.
          </h2>
        </div>
        <p className="max-w-lg text-xs leading-6 text-ink/60 sm:text-sm">
          دسته‌بندی‌های IpakToys بر اساس سبک بازی، رده سنی و تجربه موردنظر
          طراحی شده‌اند تا انتخاب برای خانواده‌ها و علاقه‌مندان بردگیم ساده‌تر
          باشد.
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map((category) => (
          <CategoryCard category={category} key={category.title} />
        ))}
      </div>
    </section>
  );
}
