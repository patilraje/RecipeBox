"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChipInput } from "@/components/ChipInput";
import { useAuth } from "@/components/AuthProvider";
import { DEFAULT_PANTRY_ITEMS } from "@/lib/storage";
import { fetchUserPantry, persistUserPantry } from "@/lib/userData";

export default function PantryPage() {
  const { user, configured } = useAuth();
  const [items, setItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchUserPantry(DEFAULT_PANTRY_ITEMS)
      .then((list) => {
        if (cancelled) return;
        setItems(list);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setItems(DEFAULT_PANTRY_ITEMS);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  async function save(next: string[]) {
    setItems(next);
    setSaving(true);
    setError(null);
    try {
      await persistUserPantry(next);
      setSavedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save pantry");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="page">
      <div className="section-intro" style={{ marginBottom: "1.25rem" }}>
        <h2>Your pantry</h2>
        <p>
          Add what you keep at home. Click the × on any item to remove it. These
          items auto-fill when you find recipes.
          {configured && !user ? (
            <>
              {" "}
              <Link href="/login">Sign in</Link> to sync across devices.
            </>
          ) : configured && user ? (
            " Synced to your account."
          ) : (
            " Saved in this browser."
          )}
        </p>
      </div>

      <section className="panel">
        {loading ? (
          <p className="muted">Loading pantry…</p>
        ) : (
          <>
            <ChipInput
              label="Pantry items"
              items={items}
              onChange={(next) => void save(next)}
              placeholder="Add an item and press Enter"
            />
            <div className="actions-row">
              <button
                type="button"
                className="secondary-button"
                disabled={saving}
                onClick={() => void save(DEFAULT_PANTRY_ITEMS)}
              >
                Reset to starter pantry
              </button>
              <Link href="/" className="primary-button">
                Find recipes with this pantry
              </Link>
            </div>
            {saving && <p className="muted">Saving…</p>}
            {!saving && savedAt && (
              <p className="muted">Saved at {savedAt}</p>
            )}
            {error && <div className="error-banner">{error}</div>}
          </>
        )}
      </section>
    </main>
  );
}
