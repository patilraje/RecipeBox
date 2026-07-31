"""API route handlers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai import AIRecipeGenerator
from app.grocery import suggest_grocery_items
from app.matcher import MatchType, contains_excluded, match_recipe
from app.models import (
    GenerateRequest,
    GenerateResponse,
    GrocerySuggestRequest,
    GrocerySuggestResponse,
    NormaliseRequest,
    NormaliseResponse,
    NormalisedIngredientOut,
    PantryDefaultsResponse,
    RecipeCard,
    SearchRequest,
    SearchResponse,
    ValidateRequest,
    ValidateResponse,
)
from app.normalizer import canonicalize_query_terms, normalize_many
from app.pantry import get_pantry_defaults
from app.providers import get_default_provider

router = APIRouter(prefix="/api")
mealdb = get_default_provider()
ai_generator = AIRecipeGenerator()

DIET_EXCLUDE_MAP: dict[str, list[str]] = {
    "vegetarian": [
        "chicken",
        "chicken breast",
        "chicken thigh",
        "beef",
        "pork",
        "lamb",
        "shrimp",
        "fish",
        "salmon",
        "bacon",
    ],
    "vegan": [
        "chicken",
        "chicken breast",
        "chicken thigh",
        "beef",
        "pork",
        "lamb",
        "shrimp",
        "fish",
        "salmon",
        "bacon",
        "egg",
        "cheese",
        "butter",
        "milk",
        "cream",
        "yogurt",
        "honey",
    ],
    "gluten-free": ["flour", "bread", "pasta", "wheat", "barley", "rye"],
    "dairy-free": ["cheese", "butter", "milk", "cream", "yogurt"],
}


def _diet_exclusions(diet: str | None, exclude_ingredients: list[str]) -> list[str]:
    extras: list[str] = []
    if diet:
        extras = DIET_EXCLUDE_MAP.get(diet.lower().strip(), [])
    return list(dict.fromkeys([*exclude_ingredients, *extras]))


def _card_from_meal(
    meal: dict,
    match,
    match_type: str,
) -> RecipeCard:
    return RecipeCard(
        id=meal["id"],
        name=meal["name"],
        image_url=meal.get("image_url"),
        cooking_time_minutes=meal.get("cooking_time_minutes"),
        servings=meal.get("servings"),
        ingredients=meal.get("ingredients") or [],
        ingredients_detailed=meal.get("ingredients_detailed") or [],
        ingredients_used=match.ingredients_used,
        pantry_spices_used=match.pantry_spices_used,
        missing_ingredients=match.missing_ingredients,
        instructions=meal.get("instructions") or [],
        source="mealdb",
        source_url=meal.get("source_url"),
        match_type=match_type,  # type: ignore[arg-type]
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/pantry/defaults", response_model=PantryDefaultsResponse)
async def pantry_defaults() -> PantryDefaultsResponse:
    data = get_pantry_defaults()
    return PantryDefaultsResponse(**data)


@router.post("/grocery/suggest", response_model=GrocerySuggestResponse)
async def grocery_suggest(body: GrocerySuggestRequest) -> GrocerySuggestResponse:
    suggestions, provider = await suggest_grocery_items(
        body.category,
        existing_items=body.existing_items,
        count=body.count,
    )
    return GrocerySuggestResponse(
        suggestions=suggestions,
        provider=provider,  # type: ignore[arg-type]
    )


@router.post("/ingredients/normalize", response_model=NormaliseResponse)
async def normalize_ingredients(body: NormaliseRequest) -> NormaliseResponse:
    items = normalize_many(body.ingredients)
    return NormaliseResponse(
        ingredients=[
            NormalisedIngredientOut(
                original=i.original,
                canonical_name=i.canonical_name,
                quantity=i.quantity,
                unit=i.unit,
                preparation=i.preparation,
            )
            for i in items
        ]
    )


@router.post("/recipes/search", response_model=SearchResponse)
async def search_recipes(body: SearchRequest) -> SearchResponse:
    excludes = _diet_exclusions(body.diet, body.exclude_ingredients)
    pantry = body.pantry_defaults

    meals = await mealdb.search_by_ingredients(
        canonicalize_query_terms(body.ingredients) or body.ingredients
    )
    exact: list[RecipeCard] = []
    near: list[RecipeCard] = []

    for meal in meals:
        ingredients = meal.get("ingredients") or []
        if contains_excluded(ingredients, excludes):
            continue
        result = match_recipe(
            ingredients,
            body.ingredients,
            pantry,
            maximum_missing=body.maximum_missing_ingredients,
        )
        if result.result_type == MatchType.EXACT:
            exact.append(_card_from_meal(meal, result, "exact_match"))
        elif result.result_type == MatchType.NEAR:
            near.append(_card_from_meal(meal, result, "near_match"))

    # Prefer fewer missing ingredients, then name
    near.sort(key=lambda r: (len(r.missing_ingredients), r.name.lower()))
    exact.sort(key=lambda r: r.name.lower())

    ai_recipes: list[RecipeCard] = []
    if body.include_ai_if_sparse and len(exact) + len(near) < body.sparse_threshold:
        if ai_generator.configured:
            try:
                generated = await ai_generator.generate_many(
                    body.ingredients,
                    pantry,
                    exclude_ingredients=excludes,
                    diet=body.diet,
                    count=1,
                )
                ai_recipes.extend(RecipeCard(**item) for item in generated)
            except Exception:
                # Search should still succeed even if AI fails
                pass

    return SearchResponse(
        exact_matches=exact,
        near_matches=near,
        ai_recipes=ai_recipes,
    )


@router.post("/recipes/generate", response_model=GenerateResponse)
async def generate_recipe(body: GenerateRequest) -> GenerateResponse:
    excludes = _diet_exclusions(body.diet, body.exclude_ingredients)
    try:
        generated = await ai_generator.generate_many(
            body.ingredients,
            body.pantry_defaults,
            exclude_ingredients=excludes,
            diet=body.diet,
            servings=body.servings,
            count=body.count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe generation failed: {exc}") from exc
    return GenerateResponse(
        recipes=[RecipeCard(**item) for item in generated],
        provider=ai_generator.last_provider,
    )


@router.post("/recipes/validate", response_model=ValidateResponse)
async def validate_recipe(body: ValidateRequest) -> ValidateResponse:
    excludes = body.exclude_ingredients
    rejected = contains_excluded(body.recipe_ingredients, excludes)
    if rejected:
        return ValidateResponse(
            result_type="reject",
            missing_ingredients=[],
            ingredients_used=[],
            pantry_spices_used=[],
            rejected_for_exclusions=True,
        )
    result = match_recipe(
        body.recipe_ingredients,
        body.user_ingredients,
        body.pantry_defaults,
        maximum_missing=body.maximum_missing_ingredients,
    )
    return ValidateResponse(
        result_type=result.result_type.value,  # type: ignore[arg-type]
        missing_ingredients=result.missing_ingredients,
        ingredients_used=result.ingredients_used,
        pantry_spices_used=result.pantry_spices_used,
        rejected_for_exclusions=False,
    )
