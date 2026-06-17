"use client";

import { SlidersHorizontal } from "lucide-react";

import type { ProductQueryParams } from "@/lib/api/products";
import { cn } from "@/lib/utils";
import type { Product } from "@/types/api";

export type FilterOption = {
  label: string;
  value: string;
};

export type ProductFilters = {
  search: string;
  category: string;
  brand: string;
  age_group: "" | Product["age_group"];
  ordering: "" | NonNullable<ProductQueryParams["ordering"]>;
};

type FilterSidebarProps = {
  filters: ProductFilters;
  categories: FilterOption[];
  brands: FilterOption[];
  onFiltersChange: (filters: ProductFilters) => void;
};

const ageGroupOptions: FilterOption[] = [
  { label: "۰ تا ۲ سال", value: "0_2" },
  { label: "۳ تا ۵ سال", value: "3_5" },
  { label: "۶ تا ۸ سال", value: "6_8" },
  { label: "۹ تا ۱۲ سال", value: "9_12" },
  { label: "۱۲ سال به بالا", value: "12_plus" },
];

const orderingOptions: FilterOption[] = [
  { label: "جدیدترین", value: "-created_at" },
  { label: "ارزان‌ترین", value: "price" },
  { label: "گران‌ترین", value: "-price" },
  { label: "قدیمی‌ترین", value: "created_at" },
];

function FilterContent({
  filters,
  categories,
  brands,
  onFiltersChange,
}: FilterSidebarProps) {
  const updateFilter = <Key extends keyof ProductFilters>(
    key: Key,
    value: ProductFilters[Key],
  ) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="space-y-7">
      <div>
        <label className="text-sm font-black text-ink" htmlFor="product-search">
          جستجو
        </label>
        <input
          className="mt-3 h-11 w-full rounded-2xl border border-ink/10 bg-white px-4 text-sm outline-none transition placeholder:text-ink/35 focus:border-coral"
          id="product-search"
          onChange={(event) => updateFilter("search", event.target.value)}
          placeholder="نام اسباب‌بازی را بنویسید"
          type="search"
          value={filters.search}
        />
      </div>

      <FilterGroup
        items={categories}
        selectedValue={filters.category}
        title="دسته‌بندی"
        onSelect={(value) => updateFilter("category", value)}
      />
      <FilterGroup
        items={brands}
        selectedValue={filters.brand}
        title="برند"
        onSelect={(value) => updateFilter("brand", value)}
      />
      <FilterGroup
        items={ageGroupOptions}
        selectedValue={filters.age_group}
        title="رده سنی"
        onSelect={(value) =>
          updateFilter("age_group", value as ProductFilters["age_group"])
        }
      />

      <div>
        <label className="text-sm font-black text-ink" htmlFor="sort-products">
          مرتب‌سازی
        </label>
        <select
          className="mt-3 h-11 w-full rounded-2xl border border-ink/10 bg-white px-4 text-sm outline-none transition focus:border-coral"
          id="sort-products"
          onChange={(event) =>
            updateFilter(
              "ordering",
              event.target.value as ProductFilters["ordering"],
            )
          }
          value={filters.ordering}
        >
          <option value="">پیش‌فرض</option>
          {orderingOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <button
        className="w-full rounded-2xl bg-cream px-4 py-3 text-sm font-black text-ink transition hover:bg-sunshine/30"
        onClick={() =>
          onFiltersChange({
            search: "",
            category: "",
            brand: "",
            age_group: "",
            ordering: "",
          })
        }
        type="button"
      >
        پاک کردن فیلترها
      </button>
    </div>
  );
}

function FilterGroup({
  title,
  items,
  selectedValue,
  onSelect,
}: {
  title: string;
  items: FilterOption[];
  selectedValue: string;
  onSelect: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-black text-ink">{title}</legend>
      <div className="mt-3 space-y-3">
        {items.map((item) => (
          <label
            className="flex cursor-pointer items-center gap-3 text-sm text-ink/65"
            key={item.value}
          >
            <input
              checked={selectedValue === item.value}
              className={cn(
                "size-4 rounded border-ink/20 text-coral focus:ring-coral",
                selectedValue === item.value && "accent-coral",
              )}
              onChange={() =>
                onSelect(selectedValue === item.value ? "" : item.value)
              }
              type="checkbox"
            />
            {item.label}
          </label>
        ))}
        {items.length === 0 ? (
          <p className="text-xs leading-6 text-ink/45">گزینه‌ای برای نمایش نیست.</p>
        ) : null}
      </div>
    </fieldset>
  );
}

export function FilterSidebar(props: FilterSidebarProps) {
  return (
    <>
      <aside className="sticky top-28 hidden h-fit rounded-[2rem] bg-white p-6 shadow-sm lg:block">
        <div className="mb-6 flex items-center gap-2">
          <SlidersHorizontal className="size-5 text-coral" />
          <h2 className="font-black text-ink">فیلتر محصولات</h2>
        </div>
        <FilterContent {...props} />
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
          <FilterContent {...props} />
        </div>
      </details>
    </>
  );
}
