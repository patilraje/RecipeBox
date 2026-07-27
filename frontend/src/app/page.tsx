"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { ChipInput } from "@/components/ChipInput";
import { useAuth } from "@/components/AuthProvider";
import { generateRecipes, searchRecipes } from "@/lib/api";
import { DEFAULT_PANTRY_ITEMS, saveLastSearch, cacheRecipe } from "@/lib/storage";
import { fetchUserPantry } from "@/lib/userData";

const DIETS = [
  { value: "", label: "No diet filter" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "vegan", label: "Vegan" },
  { value: "gluten-free", label: "Gluten-free" },
  { value: "dairy-free", label: "Dairy-free" },
];

/** Staples treated as always-available seasoning/liquid when searching. */
const SEARCH_STAPLES = ["salt", "black pepper", "water", "cooking oil"];

export default function HomePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [pending, startTransition] = useTransition();
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [excludes, setExcludes] = useState<string[]>([]);
  const [diet, setDiet] = useState("");
  const [maxMissing, setMaxMissing] = useState(2);
  const [generateCount, setGenerateCount] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [pantryLoaded, setPantryLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setPantryLoaded(false);
    fetchUserPantry(DEFAULT_PANTRY_ITEMS).then((items) => {
      if (cancelled) return;
      setIngredients(items);
      setPantryLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  function runSearch(includeAiIfSparse: boolean) {
    if (ingredients.length === 0) {
      setError("Add pantry items first, or type ingredients below.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const payload = {
          ingredients,
          pantry_defaults: SEARCH_STAPLES,
          diet: diet || null,
          exclude_ingredients: excludes,
          maximum_missing_ingredients: maxMissing,
          include_ai_if_sparse: includeAiIfSparse,
        };
        const results = await searchRecipes(payload);
        saveLastSearch(
          {
            ingredients,
            pantry_defaults: SEARCH_STAPLES,
            diet: diet || null,
            exclude_ingredients: excludes,
            maximum_missing_ingredients: maxMissing,
          },
          results,
        );
        [...results.exact_matches, ...results.near_matches, ...results.ai_recipes].forEach(
          cacheRecipe,
        );
        router.push("/results");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
      }
    });
  }

  function runGenerate() {
    if (ingredients.length === 0) {
      setError("Add pantry items first, or type ingredients below.");
      return;
    }
    setError(null);
    startTransition(async () => {
      try {
        const { recipes, provider } = await generateRecipes({
          ingredients,
          pantry_defaults: SEARCH_STAPLES,
          exclude_ingredients: excludes,
          diet: diet || null,
          count: generateCount,
        });
        const existing = {
          exact_matches: [],
          near_matches: [],
          ai_recipes: recipes,
        };
        saveLastSearch(
          {
            ingredients,
            pantry_defaults: SEARCH_STAPLES,
            diet: diet || null,
            exclude_ingredients: excludes,
            maximum_missing_ingredients: maxMissing,
          },
          existing,
        );
        recipes.forEach(cacheRecipe);
        if (provider === "template") {
          // Still navigate; user can add Groq key later for better quality
        }
        router.push("/results");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Recipe generation failed");
      }
    });
  }

  return (
    <main>
      {!showForm ? (
        <section className="hero">
          <div className="hero-content">
            <h1 className="hero-brand">RecipeBox</h1>
            <p className="hero-line">
              Find and generate recipes you can make using only the ingredients you
              already have.
            </p>
            <button
              type="button"
              className="hero-cta"
              onClick={() => setShowForm(true)}
            >
              Find recipes from my pantry
            </button>
          </div>
        </section>
      ) : (
        <div className="page">
          <section className="panel">
            <div className="section-intro">
              <h2>Available ingredients</h2>
              <p>
                Pre-filled from your{" "}
                <Link href="/pantry">Pantry</Link>. Remove with × or add extras for
                this search only.
              </p>
            </div>

            {!pantryLoaded ? (
              <p className="muted">Loading pantry…</p>
            ) : (
              <ChipInput
                label="Available from your pantry"
                items={ingredients}
                onChange={setIngredients}
                placeholder="Add an ingredient and press Enter"
              />
            )}

            <ChipInput
              label="Allergy / exclude list"
              items={excludes}
              onChange={setExcludes}
              placeholder="e.g. peanuts, shellfish"
            />

            <div className="field-block">
              <label className="field-label" htmlFor="diet">
                Dietary filter
              </label>
              <div className="select-shell">
                <select
                  id="diet"
                  value={diet}
                  onChange={(e) => setDiet(e.target.value)}
                  style={{ width: "100%", border: "none", background: "transparent" }}
                >
                  {DIETS.map((d) => (
                    <option key={d.value || "none"} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="field-block">
              <label className="field-label" htmlFor="missing">
                Allow up to {maxMissing} missing ingredient{maxMissing === 1 ? "" : "s"}
              </label>
              <input
                id="missing"
                type="range"
                min={0}
                max={2}
                value={maxMissing}
                onChange={(e) => setMaxMissing(Number(e.target.value))}
                style={{ width: "100%" }}
              />
            </div>

            <div className="field-block">
              <label className="field-label" htmlFor="gen-count">
                Generate {generateCount} recipe{generateCount === 1 ? "" : "s"}
              </label>
              <input
                id="gen-count"
                type="range"
                min={1}
                max={8}
                value={generateCount}
                onChange={(e) => setGenerateCount(Number(e.target.value))}
                style={{ width: "100%" }}
              />
            </div>
          </section>

          <div className="actions-row">
            <button
              type="button"
              className="primary-button"
              disabled={pending || !pantryLoaded}
              onClick={() => runSearch(false)}
            >
              {pending ? "Searching…" : "Find recipes"}
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={pending || !pantryLoaded}
              onClick={() => runSearch(true)}
            >
              Search + generate if sparse
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={pending || !pantryLoaded}
              onClick={runGenerate}
            >
              {pending ? "Generating…" : `Generate ${generateCount} recipe${generateCount === 1 ? "" : "s"}`}
            </button>
            <Link href="/pantry" className="secondary-button">
              Update pantry
            </Link>
          </div>

          {error && <div className="error-banner">{error}</div>}
        </div>
      )}
    </main>
  );
}
