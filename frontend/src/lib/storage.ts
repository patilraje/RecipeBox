import type { RecipeCard } from "./types";

const PANTRY_KEY = "recipebox_pantryItems";
const PANTRY_LEGACY_KEY = "recipebox_pantrySelections";
const GROCERY_KEY = "recipebox_groceryCategories";
const FAV_KEY = "recipebox_savedRecipes";
const LAST_SEARCH_KEY = "recipebox_lastSearch";
const LAST_RESULTS_KEY = "recipebox_lastResults";

export type GroceryCategory = {
  id: string;
  name: string;
  items: string[];
};

export const DEFAULT_GROCERY_CATEGORIES: GroceryCategory[] = [
  { id: "seeds", name: "Seeds", items: [] },
  { id: "snacks", name: "Snacks", items: [] },
  { id: "antioxidants", name: "Antioxidants", items: [] },
  { id: "produce", name: "Produce", items: [] },
];

export const DEFAULT_PANTRY_ITEMS = [
  "salt",
  "black pepper",
  "water",
  "cooking oil",
  "garlic",
  "onion",
  "rice",
  "tomato",
  "chicken breast",
  "eggs",
  "cheese",
];

export type LastSearch = {
  ingredients: string[];
  pantry_defaults: string[];
  diet: string | null;
  exclude_ingredients: string[];
  maximum_missing_ingredients: number;
};

function canUseStorage() {
  return typeof window !== "undefined";
}

function uniqueItems(items: string[]): string[] {
  return Array.from(
    new Map(
      items
        .map((item) => item.trim())
        .filter(Boolean)
        .map((item) => [item.toLowerCase(), item]),
    ).values(),
  );
}

export function loadUserPantry(fallback: string[] = DEFAULT_PANTRY_ITEMS): string[] {
  if (!canUseStorage()) return fallback;
  try {
    const raw = localStorage.getItem(PANTRY_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as string[];
      if (Array.isArray(parsed) && parsed.length) return uniqueItems(parsed);
    }
    // Migrate legacy shape { basic, optionalEnabled }
    const legacy = localStorage.getItem(PANTRY_LEGACY_KEY);
    if (legacy) {
      const parsed = JSON.parse(legacy) as {
        basic?: string[];
        optionalEnabled?: string[];
        items?: string[];
      };
      const merged = [
        ...(parsed.items || []),
        ...(parsed.basic || []),
        ...(parsed.optionalEnabled || []),
      ];
      const items = uniqueItems(merged);
      if (items.length) {
        saveUserPantry(items);
        return items;
      }
    }
  } catch {
    // fall through
  }
  return fallback;
}

export function saveUserPantry(items: string[]) {
  if (!canUseStorage()) return;
  localStorage.setItem(PANTRY_KEY, JSON.stringify(uniqueItems(items)));
}

function normalizeCategories(raw: unknown): GroceryCategory[] {
  if (!Array.isArray(raw)) return DEFAULT_GROCERY_CATEGORIES.map((c) => ({ ...c }));
  const cleaned: GroceryCategory[] = [];
  for (const entry of raw) {
    if (!entry || typeof entry !== "object") continue;
    const row = entry as Partial<GroceryCategory>;
    const name = typeof row.name === "string" ? row.name.trim() : "";
    if (!name) continue;
    const id =
      typeof row.id === "string" && row.id.trim()
        ? row.id.trim()
        : name.toLowerCase().replace(/\s+/g, "-");
    const items = Array.isArray(row.items)
      ? uniqueItems(row.items.filter((i): i is string => typeof i === "string"))
      : [];
    cleaned.push({ id, name, items });
  }
  return cleaned.length
    ? cleaned
    : DEFAULT_GROCERY_CATEGORIES.map((c) => ({ ...c }));
}

export function loadGroceryCategories(
  fallback: GroceryCategory[] = DEFAULT_GROCERY_CATEGORIES,
): GroceryCategory[] {
  if (!canUseStorage()) return fallback.map((c) => ({ ...c, items: [...c.items] }));
  try {
    const raw = localStorage.getItem(GROCERY_KEY);
    if (!raw) return fallback.map((c) => ({ ...c, items: [...c.items] }));
    return normalizeCategories(JSON.parse(raw));
  } catch {
    return fallback.map((c) => ({ ...c, items: [...c.items] }));
  }
}

export function saveGroceryCategories(categories: GroceryCategory[]) {
  if (!canUseStorage()) return;
  localStorage.setItem(
    GROCERY_KEY,
    JSON.stringify(normalizeCategories(categories)),
  );
}

export function loadFavourites(): RecipeCard[] {
  if (!canUseStorage()) return [];
  try {
    const raw = localStorage.getItem(FAV_KEY);
    return raw ? (JSON.parse(raw) as RecipeCard[]) : [];
  } catch {
    return [];
  }
}

export function saveFavourite(recipe: RecipeCard) {
  if (!canUseStorage()) return;
  const existing = loadFavourites().filter((r) => r.id !== recipe.id);
  localStorage.setItem(FAV_KEY, JSON.stringify([recipe, ...existing]));
}

export function removeFavourite(id: string) {
  if (!canUseStorage()) return;
  localStorage.setItem(
    FAV_KEY,
    JSON.stringify(loadFavourites().filter((r) => r.id !== id)),
  );
}

export function isFavourite(id: string): boolean {
  return loadFavourites().some((r) => r.id === id);
}

export function saveLastSearch(search: LastSearch, results: unknown) {
  if (!canUseStorage()) return;
  localStorage.setItem(LAST_SEARCH_KEY, JSON.stringify(search));
  localStorage.setItem(LAST_RESULTS_KEY, JSON.stringify(results));
}

export function loadLastSearch(): LastSearch | null {
  if (!canUseStorage()) return null;
  try {
    const raw = localStorage.getItem(LAST_SEARCH_KEY);
    return raw ? (JSON.parse(raw) as LastSearch) : null;
  } catch {
    return null;
  }
}

export function loadLastResults<T>(): T | null {
  if (!canUseStorage()) return null;
  try {
    const raw = localStorage.getItem(LAST_RESULTS_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function cacheRecipe(recipe: RecipeCard) {
  if (!canUseStorage()) return;
  const key = `recipebox_recipe_${recipe.id}`;
  localStorage.setItem(key, JSON.stringify(recipe));
}

export function loadCachedRecipe(id: string): RecipeCard | null {
  if (!canUseStorage()) return null;
  try {
    const raw = localStorage.getItem(`recipebox_recipe_${id}`);
    if (raw) return JSON.parse(raw) as RecipeCard;
    const fav = loadFavourites().find((r) => r.id === id);
    return fav || null;
  } catch {
    return null;
  }
}
