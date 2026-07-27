"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";
import { RecipeCardView } from "@/components/RecipeCardView";
import { generateRecipes } from "@/lib/api";
import {
  cacheRecipe,
  loadLastResults,
  loadLastSearch,
  saveLastSearch,
} from "@/lib/storage";
import type { RecipeCard, SearchResponse } from "@/lib/types";

export default function ResultsPage() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [generateCount, setGenerateCount] = useState(3);

  useEffect(() => {
    setResults(loadLastResults<SearchResponse>());
  }, []);

  function requestAi() {
    const search = loadLastSearch();
    if (!search) {
      setError("Run a search from the home page first.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const { recipes } = await generateRecipes({
          ingredients: search.ingredients,
          pantry_defaults: search.pantry_defaults,
          exclude_ingredients: search.exclude_ingredients,
          diet: search.diet,
          count: generateCount,
        });
        recipes.forEach(cacheRecipe);
        const next: SearchResponse = {
          exact_matches: results?.exact_matches || [],
          near_matches: results?.near_matches || [],
          ai_recipes: [...recipes, ...(results?.ai_recipes || [])],
        };
        setResults(next);
        saveLastSearch(search, next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Recipe generation failed");
      }
    });
  }

  if (!results) {
    return (
      <main className="page">
        <div className="empty-state">
          <p>No results yet.</p>
          <Link href="/" className="primary-button" style={{ display: "inline-block", marginTop: "1rem" }}>
            Start with your ingredients
          </Link>
        </div>
      </main>
    );
  }

  const sections: { title: string; description: string; items: RecipeCard[] }[] = [
    {
      title: "Exact matches",
      description: "Require no additional ingredients.",
      items: results.exact_matches,
    },
    {
      title: "Almost possible",
      description: "Missing one or two ingredients.",
      items: results.near_matches,
    },
    {
      title: "Generated recipes",
      description: "Created from only your allowed ingredients (focused subsets, not everything at once).",
      items: results.ai_recipes,
    },
  ];

  const total =
    results.exact_matches.length +
    results.near_matches.length +
    results.ai_recipes.length;

  return (
    <main className="page">
      <div className="section-intro" style={{ marginBottom: "1.5rem" }}>
        <h2>Your recipes</h2>
        <p>
          {total === 0
            ? "Nothing matched yet — try generating recipes."
            : `${total} recipe${total === 1 ? "" : "s"} that respect your pantry rules.`}
        </p>
      </div>

      <div className="panel" style={{ marginBottom: "1.25rem" }}>
        <label className="field-label" htmlFor="results-gen-count">
          Generate {generateCount} more recipe{generateCount === 1 ? "" : "s"}
        </label>
        <input
          id="results-gen-count"
          type="range"
          min={1}
          max={8}
          value={generateCount}
          onChange={(e) => setGenerateCount(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <div className="actions-row">
          <Link href="/" className="secondary-button">
            Edit ingredients
          </Link>
          <button
            type="button"
            className="primary-button"
            disabled={pending}
            onClick={requestAi}
          >
            {pending ? "Generating…" : `Generate ${generateCount}`}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {sections.map((section) => (
        <section key={section.title} className="results-section">
          <h2>{section.title}</h2>
          <p>{section.description}</p>
          {section.items.length === 0 ? (
            <p className="muted" style={{ marginTop: "0.75rem" }}>
              No recipes in this group.
            </p>
          ) : (
            <div className="results-grid">
              {section.items.map((recipe) => (
                <RecipeCardView key={recipe.id} recipe={recipe} />
              ))}
            </div>
          )}
        </section>
      ))}
    </main>
  );
}
