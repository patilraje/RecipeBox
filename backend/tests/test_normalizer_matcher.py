from app.matcher import MatchType, contains_excluded, match_recipe
from app.normalizer import normalize_ingredient


def test_normalize_onion_phrase():
    result = normalize_ingredient("two finely chopped red onions")
    assert result.canonical_name == "onion"
    assert result.quantity == 2.0
    assert result.preparation is not None
    assert "chopped" in (result.preparation or "")


def test_synonyms():
    assert normalize_ingredient("tomatoes").canonical_name == "tomato"
    assert normalize_ingredient("capsicum").canonical_name == "bell pepper"
    assert normalize_ingredient("scallion").canonical_name == "green onion"
    assert normalize_ingredient("garbanzo beans").canonical_name == "chickpea"
    assert normalize_ingredient("chilli").canonical_name == "chili"
    assert normalize_ingredient("olive oil").canonical_name == "cooking oil"


def test_exact_match():
    result = match_recipe(
        recipe_ingredients=["chicken breast", "rice", "salt", "olive oil"],
        user_ingredients=["chicken breast", "rice"],
        pantry_defaults=["salt", "black pepper", "cooking oil", "water"],
    )
    assert result.result_type == MatchType.EXACT
    assert result.missing_ingredients == []
    assert "chicken" in result.ingredients_used
    assert "cooking oil" in result.pantry_spices_used


def test_chicken_breast_normalizes_to_chicken():
    assert normalize_ingredient("chicken breast").canonical_name == "chicken"
    assert normalize_ingredient("Chicken").canonical_name == "chicken"


def test_near_match():
    result = match_recipe(
        recipe_ingredients=["chicken breast", "rice", "tomato", "onion", "salt"],
        user_ingredients=["chicken breast", "rice", "tomato"],
        pantry_defaults=["salt", "black pepper", "cooking oil"],
        maximum_missing=2,
    )
    assert result.result_type == MatchType.NEAR
    assert result.missing_ingredients == ["onion"]


def test_reject_too_many_missing():
    result = match_recipe(
        recipe_ingredients=["chicken breast", "cream", "flour", "butter", "salt"],
        user_ingredients=["chicken breast"],
        pantry_defaults=["salt"],
        maximum_missing=2,
    )
    assert result.result_type == MatchType.REJECT
    assert "cream" in result.missing_ingredients
    assert "flour" in result.missing_ingredients


def test_exclusions():
    assert contains_excluded(["chicken breast", "rice"], ["chicken breast"])
    assert not contains_excluded(["rice", "tomato"], ["chicken breast"])
