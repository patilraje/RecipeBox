"""Thin provider interface so TheMealDB can be swapped later."""

from __future__ import annotations

from typing import Any, Protocol

from app.mealdb import MealDBClient


class RecipeProvider(Protocol):
    async def search_by_ingredients(self, ingredients: list[str]) -> list[dict[str, Any]]:
        ...


def get_default_provider() -> RecipeProvider:
    return MealDBClient()
