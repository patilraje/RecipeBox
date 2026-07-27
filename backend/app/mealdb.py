"""TheMealDB API client."""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

from app.config import settings


def _split_instructions(raw: str | None) -> list[str]:
    if not raw:
        return []
    text = raw.strip()
    # Prefer numbered steps
    parts = re.split(r"\r?\n+", text)
    steps = [p.strip() for p in parts if p.strip()]
    if len(steps) == 1:
        # Split on sentence boundaries as fallback
        steps = [s.strip() for s in re.split(r"(?<=[.!?])\s+", steps[0]) if s.strip()]
    return steps


def _extract_ingredients(meal: dict[str, Any]) -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    for i in range(1, 21):
        name = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if name and str(name).strip():
            amount = str(measure).strip() if measure and str(measure).strip() else None
            items.append((str(name).strip(), amount))
    return items


def meal_to_dict(meal: dict[str, Any]) -> dict[str, Any]:
    ingredients = _extract_ingredients(meal)
    return {
        "id": f"mealdb-{meal.get('idMeal')}",
        "name": meal.get("strMeal") or "Untitled",
        "image_url": meal.get("strMealThumb"),
        "cooking_time_minutes": None,
        "servings": None,
        "ingredients": [name for name, _ in ingredients],
        "ingredients_detailed": [
            {"name": name, "amount": amount} for name, amount in ingredients
        ],
        "instructions": _split_instructions(meal.get("strInstructions")),
        "source": "mealdb",
        "source_url": meal.get("strSource") or meal.get("strYoutube"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "tags": meal.get("strTags"),
    }


class MealDBClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.mealdb_base_url).rstrip("/")

    async def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self.base_url}/{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def filter_by_ingredient(self, ingredient: str) -> list[dict[str, Any]]:
        data = await self._get("filter.php", {"i": ingredient})
        meals = data.get("meals") or []
        return meals if isinstance(meals, list) else []

    async def lookup(self, meal_id: str) -> dict[str, Any] | None:
        data = await self._get("lookup.php", {"i": meal_id})
        meals = data.get("meals") or []
        if not meals:
            return None
        return meal_to_dict(meals[0])

    async def search_by_ingredients(
        self,
        ingredients: list[str],
        *,
        max_candidates: int = 24,
        max_lookups: int = 18,
    ) -> list[dict[str, Any]]:
        """
        TheMealDB free API filters by one ingredient. We query several
        user ingredients and intersect/merge, then hydrate full recipes.
        """
        if not ingredients:
            return []

        # Prefer querying the first few distinct ingredients
        queries = ingredients[:5]
        results = await asyncio.gather(
            *[self.filter_by_ingredient(q) for q in queries],
            return_exceptions=True,
        )

        counts: dict[str, int] = {}
        thumbs: dict[str, str] = {}
        names: dict[str, str] = {}

        for result in results:
            if isinstance(result, Exception):
                continue
            for meal in result:
                meal_id = str(meal.get("idMeal"))
                if not meal_id:
                    continue
                counts[meal_id] = counts.get(meal_id, 0) + 1
                if meal.get("strMealThumb"):
                    thumbs[meal_id] = meal["strMealThumb"]
                if meal.get("strMeal"):
                    names[meal_id] = meal["strMeal"]

        # Rank by how many of our ingredient queries hit this meal
        ranked = sorted(counts.keys(), key=lambda mid: counts[mid], reverse=True)
        ranked = ranked[:max_candidates]

        lookups = await asyncio.gather(
            *[self.lookup(mid) for mid in ranked[:max_lookups]],
            return_exceptions=True,
        )

        recipes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in lookups:
            if isinstance(item, Exception) or not item:
                continue
            rid = item["id"]
            if rid in seen:
                continue
            seen.add(rid)
            recipes.append(item)
        return recipes
