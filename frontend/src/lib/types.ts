export type RecipeIngredient = {
  name: string;
  amount?: string | null;
};

export type RecipeCard = {
  id: string;
  name: string;
  image_url?: string | null;
  cooking_time_minutes?: number | null;
  servings?: number | null;
  ingredients: string[];
  ingredients_detailed: RecipeIngredient[];
  ingredients_used: string[];
  pantry_spices_used: string[];
  missing_ingredients: string[];
  instructions: string[];
  source: "mealdb" | "ai";
  source_url?: string | null;
  match_type?: "exact_match" | "near_match" | "ai_created" | null;
};

export type SearchResponse = {
  exact_matches: RecipeCard[];
  near_matches: RecipeCard[];
  ai_recipes: RecipeCard[];
};

export type PantryDefaults = {
  basic: string[];
  optional: string[];
};

export type SearchPayload = {
  ingredients: string[];
  pantry_defaults: string[];
  diet: string | null;
  exclude_ingredients: string[];
  maximum_missing_ingredients: number;
  include_ai_if_sparse: boolean;
};
