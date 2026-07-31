"""Pydantic request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class NormaliseRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1)


class NormalisedIngredientOut(BaseModel):
    original: str
    canonical_name: str
    quantity: float | None = None
    unit: str | None = None
    preparation: str | None = None


class NormaliseResponse(BaseModel):
    ingredients: list[NormalisedIngredientOut]


class RecipeIngredient(BaseModel):
    name: str
    amount: str | None = None


class RecipeCard(BaseModel):
    id: str
    name: str
    image_url: str | None = None
    cooking_time_minutes: int | None = None
    servings: int | None = None
    ingredients: list[str]
    ingredients_detailed: list[RecipeIngredient] = []
    ingredients_used: list[str] = []
    pantry_spices_used: list[str] = []
    missing_ingredients: list[str] = []
    instructions: list[str] = []
    source: Literal["mealdb", "ai"]
    source_url: str | None = None
    match_type: Literal["exact_match", "near_match", "ai_created"] | None = None


class SearchRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1)
    pantry_defaults: list[str] = []
    diet: str | None = None
    exclude_ingredients: list[str] = []
    maximum_missing_ingredients: int = 2
    include_ai_if_sparse: bool = False
    sparse_threshold: int = 2


class SearchResponse(BaseModel):
    exact_matches: list[RecipeCard]
    near_matches: list[RecipeCard]
    ai_recipes: list[RecipeCard] = []


class GenerateRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1)
    pantry_defaults: list[str] = []
    exclude_ingredients: list[str] = []
    diet: str | None = None
    servings: int = 2
    count: int = Field(default=1, ge=1, le=8)


class GenerateResponse(BaseModel):
    recipes: list[RecipeCard]
    provider: Literal["gemini", "groq", "ollama", "template"]


class ValidateRequest(BaseModel):
    recipe_ingredients: list[str]
    user_ingredients: list[str]
    pantry_defaults: list[str] = []
    maximum_missing_ingredients: int = 2
    exclude_ingredients: list[str] = []


class ValidateResponse(BaseModel):
    result_type: Literal["exact_match", "near_match", "reject"]
    missing_ingredients: list[str]
    ingredients_used: list[str]
    pantry_spices_used: list[str]
    rejected_for_exclusions: bool = False


class PantryDefaultsResponse(BaseModel):
    basic: list[str]
    optional: list[str]


class GrocerySuggestRequest(BaseModel):
    category: str = Field(min_length=1)
    existing_items: list[str] = []
    count: int = Field(default=8, ge=1, le=16)


class GrocerySuggestResponse(BaseModel):
    suggestions: list[str]
    provider: Literal["gemini", "groq", "ollama", "template"]
