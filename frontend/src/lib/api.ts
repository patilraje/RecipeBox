import type { PantryDefaults, RecipeCard, SearchPayload, SearchResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type GenerateResponse = {
  recipes: RecipeCard[];
  provider: "gemini" | "groq" | "ollama" | "template";
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return response.json() as Promise<T>;
}

export function getPantryDefaults() {
  return request<PantryDefaults>("/api/pantry/defaults");
}

export function searchRecipes(payload: SearchPayload) {
  return request<SearchResponse>("/api/recipes/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateRecipes(payload: {
  ingredients: string[];
  pantry_defaults: string[];
  exclude_ingredients: string[];
  diet: string | null;
  servings?: number;
  count?: number;
}) {
  return request<GenerateResponse>("/api/recipes/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { API_URL };
