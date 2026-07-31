"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ChipInput } from "@/components/ChipInput";
import { useAuth } from "@/components/AuthProvider";
import { suggestGroceryItems } from "@/lib/api";
import {
  DEFAULT_GROCERY_CATEGORIES,
  type GroceryCategory,
} from "@/lib/storage";
import { fetchGroceryList, persistGroceryList } from "@/lib/userData";

function newCategoryId(name: string) {
  const base = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `${base || "category"}-${Date.now().toString(36)}`;
}

export default function GroceryPage() {
  const { user, configured } = useAuth();
  const [categories, setCategories] = useState<GroceryCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [suggestingId, setSuggestingId] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<
    Record<string, { items: string[]; provider: string }>
  >({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchGroceryList(DEFAULT_GROCERY_CATEGORIES)
      .then((list) => {
        if (cancelled) return;
        setCategories(list);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setCategories(DEFAULT_GROCERY_CATEGORIES.map((c) => ({ ...c, items: [] })));
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  async function save(next: GroceryCategory[]) {
    setCategories(next);
    setSaving(true);
    setError(null);
    try {
      await persistGroceryList(next);
      setSavedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save grocery list");
    } finally {
      setSaving(false);
    }
  }

  function updateCategoryItems(id: string, items: string[]) {
    void save(
      categories.map((cat) => (cat.id === id ? { ...cat, items } : cat)),
    );
  }

  function addCategory(e: FormEvent) {
    e.preventDefault();
    const name = newCategoryName.trim();
    if (!name) return;
    const exists = categories.some(
      (c) => c.name.toLowerCase() === name.toLowerCase(),
    );
    if (exists) {
      setNewCategoryName("");
      return;
    }
    setNewCategoryName("");
    void save([
      ...categories,
      { id: newCategoryId(name), name, items: [] },
    ]);
  }

  function removeCategory(id: string) {
    const nextSuggestions = { ...suggestions };
    delete nextSuggestions[id];
    setSuggestions(nextSuggestions);
    void save(categories.filter((c) => c.id !== id));
  }

  async function suggestFor(category: GroceryCategory) {
    setSuggestingId(category.id);
    setError(null);
    try {
      const result = await suggestGroceryItems({
        category: category.name,
        existing_items: category.items,
        count: 8,
      });
      const existing = new Set(
        category.items.map((i) => i.toLowerCase()),
      );
      const items = result.suggestions.filter(
        (s) => !existing.has(s.toLowerCase()),
      );
      setSuggestions((prev) => ({
        ...prev,
        [category.id]: { items, provider: result.provider },
      }));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load suggestions",
      );
    } finally {
      setSuggestingId(null);
    }
  }

  function acceptSuggestion(categoryId: string, item: string) {
    const category = categories.find((c) => c.id === categoryId);
    if (!category) return;
    const exists = category.items.some(
      (i) => i.toLowerCase() === item.toLowerCase(),
    );
    if (exists) {
      setSuggestions((prev) => ({
        ...prev,
        [categoryId]: {
          ...prev[categoryId],
          items: (prev[categoryId]?.items || []).filter(
            (s) => s.toLowerCase() !== item.toLowerCase(),
          ),
          provider: prev[categoryId]?.provider || "template",
        },
      }));
      return;
    }
    setSuggestions((prev) => ({
      ...prev,
      [categoryId]: {
        ...prev[categoryId],
        items: (prev[categoryId]?.items || []).filter(
          (s) => s.toLowerCase() !== item.toLowerCase(),
        ),
        provider: prev[categoryId]?.provider || "template",
      },
    }));
    void save(
      categories.map((cat) =>
        cat.id === categoryId
          ? { ...cat, items: [...cat.items, item] }
          : cat,
      ),
    );
  }

  return (
    <main className="page">
      <div className="section-intro" style={{ marginBottom: "1.25rem" }}>
        <h2>Grocery list</h2>
        <p>
          Keep a categorized shopping list — seeds, snacks, antioxidants, and
          anything else you track. Use Suggest for AI ideas, then tap + to add
          only what you want.
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

      {loading ? (
        <section className="panel">
          <p className="muted">Loading grocery list…</p>
        </section>
      ) : (
        <>
          {categories.map((category) => {
            const pending = suggestions[category.id];
            return (
              <section key={category.id} className="panel grocery-category">
                <div className="grocery-category-head">
                  <h3>{category.name}</h3>
                  <div className="grocery-category-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={suggestingId === category.id}
                      onClick={() => void suggestFor(category)}
                    >
                      {suggestingId === category.id
                        ? "Suggesting…"
                        : "Suggest"}
                    </button>
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => removeCategory(category.id)}
                    >
                      Remove category
                    </button>
                  </div>
                </div>

                <ChipInput
                  label={`${category.name} items`}
                  items={category.items}
                  onChange={(items) => updateCategoryItems(category.id, items)}
                  placeholder="Add an item and press Enter"
                />

                {pending && pending.items.length > 0 && (
                  <div className="grocery-suggestions">
                    <p className="muted">
                      Suggestions
                      {pending.provider === "gemini"
                        ? " (AI)"
                        : " (starter list)"}
                      — tap + to add
                    </p>
                    <div className="chip-row">
                      {pending.items.map((item) => (
                        <button
                          key={item}
                          type="button"
                          className="chip chip-suggest"
                          onClick={() => acceptSuggestion(category.id, item)}
                          aria-label={`Add ${item}`}
                        >
                          {item}
                          <span aria-hidden>+</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {pending && pending.items.length === 0 && (
                  <p className="muted">No new suggestions — try again later.</p>
                )}
              </section>
            );
          })}

          <section className="panel">
            <form className="actions-row" onSubmit={addCategory}>
              <input
                className="text-input grocery-category-input"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                placeholder="New category name"
                aria-label="New category name"
              />
              <button type="submit" className="secondary-button">
                Add category
              </button>
            </form>
            {saving && <p className="muted">Saving…</p>}
            {!saving && savedAt && (
              <p className="muted">Saved at {savedAt}</p>
            )}
            {error && <div className="error-banner">{error}</div>}
          </section>
        </>
      )}
    </main>
  );
}
