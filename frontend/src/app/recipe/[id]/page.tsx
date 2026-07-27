"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  loadCachedRecipe,
} from "@/lib/storage";
import {
  deleteFavourite,
  favouriteExists,
  persistFavourite,
} from "@/lib/userData";
import type { RecipeCard } from "@/lib/types";

export default function RecipeDetailPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(params.id);
  const [recipe, setRecipe] = useState<RecipeCard | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const found = loadCachedRecipe(id);
    setRecipe(found);
    void favouriteExists(id).then(setSaved);
  }, [id]);

  if (!recipe) {
    return (
      <main className="page">
        <div className="empty-state">
          <p>Recipe not found in this browser session.</p>
          <Link href="/results" className="primary-button" style={{ display: "inline-block", marginTop: "1rem" }}>
            Back to results
          </Link>
        </div>
      </main>
    );
  }

  async function toggleSave() {
    if (!recipe) return;
    if (saved) {
      await deleteFavourite(recipe.id);
      setSaved(false);
    } else {
      await persistFavourite(recipe);
      setSaved(true);
    }
  }

  const detailed =
    recipe.ingredients_detailed?.length > 0
      ? recipe.ingredients_detailed
      : recipe.ingredients.map((name) => ({ name, amount: null }));

  return (
    <main className="page">
      <div className="detail-layout">
        <div className="detail-media">
          {recipe.image_url ? (
            <Image
              src={recipe.image_url}
              alt={recipe.name}
              fill
              sizes="(max-width: 860px) 100vw, 50vw"
              unoptimized
            />
          ) : (
            <div className="recipe-image-fallback" aria-hidden>
              <span>{recipe.name.slice(0, 1)}</span>
            </div>
          )}
        </div>

        <div>
          <div className="detail-header">
            <div className="recipe-meta">
              <span className={`source-badge ${recipe.source}`}>
                {recipe.source === "ai" ? "Generated" : "Found online"}
              </span>
              {recipe.cooking_time_minutes ? (
                <span className="time-badge">{recipe.cooking_time_minutes} min</span>
              ) : null}
              {recipe.servings ? (
                <span className="time-badge">{recipe.servings} servings</span>
              ) : null}
            </div>
            <h1>{recipe.name}</h1>
            {recipe.source_url && (
              <p className="muted">
                Source:{" "}
                <a href={recipe.source_url} target="_blank" rel="noreferrer">
                  original recipe
                </a>
              </p>
            )}
          </div>

          <div className="detail-actions">
            <button type="button" className="primary-button" onClick={toggleSave}>
              {saved ? "Remove from saved" : "Save favourite"}
            </button>
            <Link href="/results" className="secondary-button">
              Back to results
            </Link>
          </div>

          {recipe.missing_ingredients.length > 0 && (
            <p className="missing">
              Missing: {recipe.missing_ingredients.join(", ")}
            </p>
          )}

          <div className="list-block">
            <h2>Ingredients used</h2>
            <ul>
              {detailed.map((item, index) => (
                <li key={`${item.name}-${index}`}>
                  {item.amount ? `${item.amount} ` : ""}
                  {item.name}
                </li>
              ))}
            </ul>
          </div>

          {recipe.pantry_spices_used.length > 0 && (
            <div className="list-block">
              <h2>Pantry spices used</h2>
              <ul>
                {recipe.pantry_spices_used.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="list-block">
            <h2>Instructions</h2>
            <ol>
              {recipe.instructions.map((step, index) => (
                <li key={`${index}-${step.slice(0, 12)}`}>{step}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </main>
  );
}
