import { apiClient } from "@/lib/api/client";
import type {
  HomepageProductSlot,
  HomepageSectionKey,
  HomepageSectionsResponse,
} from "@/types/api";

const emptySections: HomepageSectionsResponse = {
  hero_slider: [],
  popular_marquee: [],
  latest_carousel: [],
  board_games: [],
  construction: [],
  featured_products: [],
  educational: [],
};

export function getHomepageSections() {
  return apiClient.get<HomepageSectionsResponse>("/homepage/sections/");
}

export function getHomepageSectionProducts(
  sections: HomepageSectionsResponse,
  section: HomepageSectionKey,
) {
  return (sections[section] || [])
    .map((slot) => slot.product)
    .filter((product) => product?.slug);
}

export function normalizeHomepageSections(
  sections?: Partial<HomepageSectionsResponse> | null,
): HomepageSectionsResponse {
  return {
    ...emptySections,
    ...(sections || {}),
  };
}

export function getHomepageSectionSlots(
  sections: HomepageSectionsResponse,
  section: HomepageSectionKey,
): HomepageProductSlot[] {
  return sections[section] || [];
}
