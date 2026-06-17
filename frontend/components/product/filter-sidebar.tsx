import { SlidersHorizontal } from "lucide-react";

import { ageGroups, brands, categories } from "@/lib/mock-data";

function FilterContent() {
  return (
    <div className="space-y-7">
      <div>
        <label className="text-sm font-black text-ink" htmlFor="product-search">
          جستجو
        </label>
        <input
          className="mt-3 h-11 w-full rounded-2xl border border-ink/10 bg-white px-4 text-sm outline-none transition placeholder:text-ink/35 focus:border-coral"
          id="product-search"
          placeholder="نام اسباب‌بازی را بنویسید"
          type="search"
        />
      </div>

      <FilterGroup
        items={categories.map((category) => category.title)}
        title="دسته‌بندی"
      />
      <FilterGroup items={brands.map((brand) => brand.name)} title="برند" />
      <FilterGroup items={ageGroups} title="رده سنی" />

      <div>
        <label className="text-sm font-black text-ink" htmlFor="sort-products">
          مرتب‌سازی
        </label>
        <select
          className="mt-3 h-11 w-full rounded-2xl border border-ink/10 bg-white px-4 text-sm outline-none transition focus:border-coral"
          id="sort-products"
          defaultValue="newest"
        >
          <option value="newest">جدیدترین</option>
          <option value="popular">محبوب‌ترین</option>
          <option value="price-low">ارزان‌ترین</option>
          <option value="price-high">گران‌ترین</option>
        </select>
      </div>
    </div>
  );
}

function FilterGroup({ title, items }: { title: string; items: string[] }) {
  return (
    <fieldset>
      <legend className="text-sm font-black text-ink">{title}</legend>
      <div className="mt-3 space-y-3">
        {items.map((item) => (
          <label
            className="flex cursor-pointer items-center gap-3 text-sm text-ink/65"
            key={item}
          >
            <input
              className="size-4 rounded border-ink/20 text-coral focus:ring-coral"
              type="checkbox"
            />
            {item}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function FilterSidebar() {
  return (
    <>
      <aside className="sticky top-28 hidden h-fit rounded-[2rem] bg-white p-6 shadow-sm lg:block">
        <div className="mb-6 flex items-center gap-2">
          <SlidersHorizontal className="size-5 text-coral" />
          <h2 className="font-black text-ink">فیلتر محصولات</h2>
        </div>
        <FilterContent />
      </aside>

      <details className="rounded-[2rem] bg-white p-4 shadow-sm lg:hidden">
        <summary className="flex cursor-pointer list-none items-center justify-between font-black text-ink">
          <span className="flex items-center gap-2">
            <SlidersHorizontal className="size-5 text-coral" />
            فیلتر و مرتب‌سازی
          </span>
          <span className="text-sm text-coral">باز کردن</span>
        </summary>
        <div className="mt-6">
          <FilterContent />
        </div>
      </details>
    </>
  );
}
