import type { RecipeCard } from "./types";
import { getSupabase } from "./supabase";
import {
  loadFavourites as loadLocalFavourites,
  loadUserPantry as loadLocalPantry,
  loadGroceryCategories as loadLocalGrocery,
  saveFavourite as saveLocalFavourite,
  saveUserPantry as saveLocalPantry,
  saveGroceryCategories as saveLocalGrocery,
  removeFavourite as removeLocalFavourite,
  DEFAULT_PANTRY_ITEMS,
  DEFAULT_GROCERY_CATEGORIES,
  type GroceryCategory,
} from "./storage";

export async function fetchUserPantry(
  fallback: string[] = DEFAULT_PANTRY_ITEMS,
): Promise<string[]> {
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };

  if (!supabase || !user) {
    return loadLocalPantry(fallback);
  }

  const { data, error } = await supabase
    .from("pantry_settings")
    .select("basic, optional_enabled")
    .eq("user_id", user.id)
    .maybeSingle();

  if (error || !data) {
    const local = loadLocalPantry(fallback);
    const { error: upsertError } = await supabase.from("pantry_settings").upsert({
      user_id: user.id,
      basic: local,
      optional_enabled: [],
      updated_at: new Date().toISOString(),
    });
    if (upsertError) {
      // Table may not exist yet — still return local pantry
      console.warn("pantry sync:", upsertError.message);
    }
    return local;
  }

  // Prefer basic as the full pantry list; merge legacy optional_enabled if present
  const merged = [
    ...(data.basic || []),
    ...(data.optional_enabled || []),
  ];
  const unique = Array.from(
    new Map(merged.map((item) => [item.toLowerCase(), item])).values(),
  );
  return unique.length ? unique : fallback;
}

export async function persistUserPantry(items: string[]) {
  saveLocalPantry(items);
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };
  if (!supabase || !user) return;

  const { error } = await supabase.from("pantry_settings").upsert({
    user_id: user.id,
    basic: items,
    optional_enabled: [],
    updated_at: new Date().toISOString(),
  });
  if (error) {
    throw new Error(
      error.message.includes("Could not find") || error.code === "42P01"
        ? "Pantry table missing — run supabase/schema.sql in the Supabase SQL Editor."
        : `Could not sync pantry: ${error.message}`,
    );
  }
}

export async function fetchGroceryList(
  fallback: GroceryCategory[] = DEFAULT_GROCERY_CATEGORIES,
): Promise<GroceryCategory[]> {
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };

  if (!supabase || !user) {
    return loadLocalGrocery(fallback);
  }

  const { data, error } = await supabase
    .from("grocery_lists")
    .select("categories")
    .eq("user_id", user.id)
    .maybeSingle();

  if (error || !data) {
    const local = loadLocalGrocery(fallback);
    const { error: upsertError } = await supabase.from("grocery_lists").upsert({
      user_id: user.id,
      categories: local,
      updated_at: new Date().toISOString(),
    });
    if (upsertError) {
      console.warn("grocery sync:", upsertError.message);
    }
    return local;
  }

  const categories = Array.isArray(data.categories)
    ? (data.categories as GroceryCategory[])
    : [];
  if (!categories.length) return loadLocalGrocery(fallback);
  saveLocalGrocery(categories);
  return loadLocalGrocery();
}

export async function persistGroceryList(categories: GroceryCategory[]) {
  saveLocalGrocery(categories);
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };
  if (!supabase || !user) return;

  const { error } = await supabase.from("grocery_lists").upsert({
    user_id: user.id,
    categories,
    updated_at: new Date().toISOString(),
  });
  if (error) {
    throw new Error(
      error.message.includes("Could not find") || error.code === "42P01"
        ? "Grocery table missing — run supabase/schema.sql in the Supabase SQL Editor."
        : `Could not sync grocery list: ${error.message}`,
    );
  }
}

export async function fetchFavourites(): Promise<RecipeCard[]> {
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };

  if (!supabase || !user) {
    return loadLocalFavourites();
  }

  const { data, error } = await supabase
    .from("saved_recipes")
    .select("recipe")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  if (error || !data) return loadLocalFavourites();
  return data.map((row) => row.recipe as RecipeCard);
}

export async function persistFavourite(recipe: RecipeCard) {
  saveLocalFavourite(recipe);
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };
  if (!supabase || !user) return;

  await supabase.from("saved_recipes").upsert(
    {
      user_id: user.id,
      recipe_id: recipe.id,
      recipe,
    },
    { onConflict: "user_id,recipe_id" },
  );
}

export async function deleteFavourite(recipeId: string) {
  removeLocalFavourite(recipeId);
  const supabase = getSupabase();
  const {
    data: { user },
  } = (await supabase?.auth.getUser()) || { data: { user: null } };
  if (!supabase || !user) return;

  await supabase
    .from("saved_recipes")
    .delete()
    .eq("user_id", user.id)
    .eq("recipe_id", recipeId);
}

export async function favouriteExists(recipeId: string): Promise<boolean> {
  const items = await fetchFavourites();
  return items.some((r) => r.id === recipeId);
}
