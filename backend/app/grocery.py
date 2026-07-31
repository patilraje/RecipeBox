"""Grocery category suggestions via Gemini with keyword fallback."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import settings

FALLBACK_BY_CATEGORY: dict[str, list[str]] = {
    "seeds": [
        "chia seeds",
        "flax seeds",
        "pumpkin seeds",
        "sunflower seeds",
        "hemp seeds",
        "sesame seeds",
    ],
    "snacks": [
        "almonds",
        "walnuts",
        "rice cakes",
        "popcorn",
        "apple slices",
        "hummus",
        "carrot sticks",
    ],
    "antioxidants": [
        "blueberries",
        "strawberries",
        "spinach",
        "kale",
        "dark chocolate",
        "green tea",
        "pecans",
        "artichokes",
    ],
    "produce": [
        "broccoli",
        "spinach",
        "bell peppers",
        "tomatoes",
        "carrots",
        "cucumber",
        "avocado",
        "berries",
    ],
    "veggies": [
        "broccoli",
        "spinach",
        "kale",
        "zucchini",
        "carrots",
        "cauliflower",
        "cabbage",
        "green beans",
    ],
    "protein": [
        "eggs",
        "chicken breast",
        "tofu",
        "greek yogurt",
        "lentils",
        "chickpeas",
        "canned tuna",
    ],
    "dairy": ["milk", "yogurt", "cheese", "butter", "cottage cheese"],
    "grains": ["oats", "brown rice", "quinoa", "whole wheat bread", "pasta"],
}


def _fallback_suggestions(category: str, existing: set[str], count: int) -> list[str]:
    key = category.strip().lower()
    candidates: list[str] = []
    for name, items in FALLBACK_BY_CATEGORY.items():
        if name in key or key in name:
            candidates.extend(items)
    if not candidates:
        candidates = [
            "bananas",
            "oats",
            "spinach",
            "eggs",
            "yogurt",
            "almonds",
            "olive oil",
            "beans",
        ]
    out: list[str] = []
    for item in candidates:
        if item.lower() in existing:
            continue
        out.append(item)
        if len(out) >= count:
            break
    return out


def _parse_suggestions(content: str, count: int) -> list[str]:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        items = parsed.get("suggestions") or parsed.get("items") or []
    elif isinstance(parsed, list):
        items = parsed
    else:
        items = []
    cleaned: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        name = item.strip()
        if not name:
            continue
        cleaned.append(name)
        if len(cleaned) >= count:
            break
    return cleaned


async def _call_gemini_suggestions(
    category: str,
    existing_items: list[str],
    count: int,
) -> list[str]:
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    model = settings.gemini_model
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    existing = ", ".join(existing_items) if existing_items else "(none)"
    prompt = f"""Suggest {count} grocery foods for this shopping category: "{category}".

Already on the list (do not repeat): {existing}

Rules:
- Return real grocery foods/ingredients people buy, not recipes or brands.
- Keep names short and specific (e.g. "chia seeds", "blueberries").
- Prefer variety within the category.
- Respond with JSON only: {{"suggestions":["item1","item2"]}}
"""
    body: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            url,
            params={"key": settings.google_api_key},
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
    parts = payload["candidates"][0]["content"]["parts"]
    content = "".join(p.get("text", "") for p in parts)
    return _parse_suggestions(content, count)


async def suggest_grocery_items(
    category: str,
    existing_items: list[str] | None = None,
    count: int = 8,
) -> tuple[list[str], str]:
    count = max(1, min(16, count))
    existing = existing_items or []
    existing_set = {i.strip().lower() for i in existing if i.strip()}

    if settings.google_api_key:
        try:
            suggestions = await _call_gemini_suggestions(category, existing, count)
            filtered = [
                s for s in suggestions if s.strip().lower() not in existing_set
            ]
            if filtered:
                return filtered[:count], "gemini"
        except Exception:
            pass

    return _fallback_suggestions(category, existing_set, count), "template"
