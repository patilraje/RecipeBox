"use client";

import Image from "next/image";
import Link from "next/link";
import type { RecipeCard as Recipe } from "@/lib/types";
import { cacheRecipe } from "@/lib/storage";

type Props = {
  recipe: Recipe;
};

function sourceLabel(recipe: Recipe) {
  if (recipe.source === "ai") return "Generated";
  return "Found online";
}

export function RecipeCardView({ recipe }: Props) {
  function openRecipe() {
    cacheRecipe(recipe);
  }

  return (
    <article className="recipe-card">
      <Link href={`/recipe/${encodeURIComponent(recipe.id)}`} onClick={openRecipe} className="recipe-card-link">
        <div className="recipe-media">
          {recipe.image_url ? (
            <Image
              src={recipe.image_url}
              alt={recipe.name}
              fill
              sizes="(max-width: 768px) 100vw, 33vw"
              className="recipe-image"
              unoptimized
            />
          ) : (
            <div className="recipe-image-fallback" aria-hidden>
              <span>{recipe.name.slice(0, 1)}</span>
            </div>
          )}
        </div>
        <div className="recipe-body">
          <div className="recipe-meta">
            <span className={`source-badge ${recipe.source}`}>{sourceLabel(recipe)}</span>
            {recipe.cooking_time_minutes ? (
              <span className="time-badge">{recipe.cooking_time_minutes} min</span>
            ) : null}
          </div>
          <h3>{recipe.name}</h3>
          {recipe.missing_ingredients.length > 0 ? (
            <p className="missing">
              Missing: {recipe.missing_ingredients.join(", ")}
            </p>
          ) : (
            <p className="ready">Uses only what you have</p>
          )}
          {recipe.pantry_spices_used.length > 0 && (
            <p className="pantry-used">
              Pantry: {recipe.pantry_spices_used.slice(0, 4).join(", ")}
              {recipe.pantry_spices_used.length > 4 ? "…" : ""}
            </p>
          )}
        </div>
      </Link>
    </article>
  );
}
