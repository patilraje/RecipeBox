"""Recipe ingredient matching against user + pantry allowed sets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.normalizer import canonical_set


class MatchType(str, Enum):
    EXACT = "exact_match"
    NEAR = "near_match"
    REJECT = "reject"


@dataclass
class MatchResult:
    result_type: MatchType
    missing_ingredients: list[str]
    ingredients_used: list[str]
    pantry_spices_used: list[str]
    required_ingredients: list[str]


def match_recipe(
    recipe_ingredients: list[str],
    user_ingredients: list[str],
    pantry_defaults: list[str],
    maximum_missing: int = 2,
) -> MatchResult:
    """
    allowed = user + pantry
    required = recipe_ingredients - pantry
    missing = required - allowed  (equiv. required - user, since pantry already removed)
    """
    pantry = canonical_set(pantry_defaults)
    user = canonical_set(user_ingredients)
    allowed = user | pantry
    recipe = canonical_set(recipe_ingredients)

    required = recipe - pantry
    missing = sorted(required - allowed)
    ingredients_used = sorted(recipe & user)
    pantry_used = sorted(recipe & pantry)

    if len(missing) == 0:
        result_type = MatchType.EXACT
    elif len(missing) <= maximum_missing:
        result_type = MatchType.NEAR
    else:
        result_type = MatchType.REJECT

    return MatchResult(
        result_type=result_type,
        missing_ingredients=missing,
        ingredients_used=ingredients_used,
        pantry_spices_used=pantry_used,
        required_ingredients=sorted(required),
    )


def contains_excluded(recipe_ingredients: list[str], exclude_ingredients: list[str]) -> bool:
    if not exclude_ingredients:
        return False
    recipe = canonical_set(recipe_ingredients)
    excluded = canonical_set(exclude_ingredients)
    return bool(recipe & excluded)
