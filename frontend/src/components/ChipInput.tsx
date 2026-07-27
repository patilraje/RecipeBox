"use client";

import { FormEvent, KeyboardEvent, useState } from "react";

type Props = {
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  label: string;
};

export function ChipInput({ items, onChange, placeholder, label }: Props) {
  const [draft, setDraft] = useState("");

  function addItem(value: string) {
    const trimmed = value.trim();
    if (!trimmed) return;
    const exists = items.some((i) => i.toLowerCase() === trimmed.toLowerCase());
    if (exists) {
      setDraft("");
      return;
    }
    onChange([...items, trimmed]);
    setDraft("");
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    addItem(draft);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addItem(draft.replace(/,/g, ""));
    } else if (e.key === "Backspace" && !draft && items.length) {
      onChange(items.slice(0, -1));
    }
  }

  return (
    <div className="field-block">
      <label className="field-label">{label}</label>
      <form className="chip-shell" onSubmit={onSubmit}>
        <div className="chip-row">
          {items.map((item) => (
            <button
              key={item}
              type="button"
              className="chip"
              onClick={() => onChange(items.filter((i) => i !== item))}
              aria-label={`Remove ${item}`}
            >
              {item}
              <span aria-hidden>×</span>
            </button>
          ))}
          <input
            className="chip-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            aria-label={label}
          />
        </div>
      </form>
    </div>
  );
}
