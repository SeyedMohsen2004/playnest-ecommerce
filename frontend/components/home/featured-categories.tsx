import { CategoryCard } from "@/components/home/category-card";
import { categories } from "@/lib/mock-data";

export function FeaturedCategories() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8" id="categories">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-coral">
            Featured categories
          </p>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-ink sm:text-4xl">
            Find the right toy faster.
          </h2>
        </div>
        <p className="max-w-xl text-sm leading-6 text-ink/60">
          Explore playful categories designed around age, interests, creativity,
          and everyday family fun.
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {categories.map((category) => (
          <CategoryCard category={category} key={category.title} />
        ))}
      </div>
    </section>
  );
}
