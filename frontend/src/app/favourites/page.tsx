"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RecipeCardView } from "@/components/RecipeCardView";
import { useAuth } from "@/components/AuthProvider";
import { deleteFavourite, fetchFavourites } from "@/lib/userData";
import type { RecipeCard } from "@/lib/types";

export default function FavouritesPage() {
  const { user, configured } = useAuth();
  const [items, setItems] = useState<RecipeCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchFavourites().then((list) => {
      if (cancelled) return;
      setItems(list);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  async function clearOne(id: string) {
    await deleteFavourite(id);
    setItems(await fetchFavourites());
  }

  return (
    <main className="page">
      <div className="section-intro" style={{ marginBottom: "1.5rem" }}>
        <h2>Saved favourites</h2>
        <p>
          {configured && user
            ? "Synced to your Supabase account."
            : configured
              ? "Stored in this browser — sign in to sync across devices."
              : "Stored in this browser only."}
          {configured && !user ? (
            <>
              {" "}
              <Link href="/login">Sign in</Link>
            </>
          ) : null}
        </p>
      </div>

      {loading ? (
        <p className="muted">Loading saved recipes…</p>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <p>No favourites yet.</p>
          <Link
            href="/"
            className="primary-button"
            style={{ display: "inline-block", marginTop: "1rem" }}
          >
            Find recipes
          </Link>
        </div>
      ) : (
        <div className="results-grid">
          {items.map((recipe) => (
            <div key={recipe.id}>
              <RecipeCardView recipe={recipe} />
              <button
                type="button"
                className="text-button"
                style={{ marginTop: "0.55rem" }}
                onClick={() => clearOne(recipe.id)}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
