import pytest

from app.ai import AIRecipeGenerator
from app.matcher import MatchType, match_recipe


@pytest.mark.asyncio
async def test_template_generate_many_uses_subsets():
    gen = AIRecipeGenerator()
    user = ["chicken breast", "rice", "tomato", "onion", "egg", "cheese", "potato"]
    pantry = ["salt", "black pepper", "cooking oil", "water", "paprika", "cumin"]
    recipes = await gen.generate_many(
        user, pantry, exclude_ingredients=[], servings=2, count=4
    )
    assert 1 <= len(recipes) <= 4
    titles = {r["name"] for r in recipes}
    assert len(titles) >= 1
    for recipe in recipes:
        result = match_recipe(
            recipe["ingredients"], user, pantry, maximum_missing=0
        )
        assert result.result_type == MatchType.EXACT
        # Should not dump the entire pantry+user list into one recipe
        assert len(recipe["ingredients"]) < len(user) + len(pantry)


@pytest.mark.asyncio
async def test_generate_respects_exclusions():
    gen = AIRecipeGenerator()
    user = ["chicken", "rice", "tomato", "onion", "cheese"]
    pantry = ["salt", "black pepper", "cooking oil"]
    recipes = await gen.generate_many(
        user,
        pantry,
        exclude_ingredients=["cheese"],
        servings=2,
        count=2,
    )
    for recipe in recipes:
        assert "cheese" not in [i.lower() for i in recipe["ingredients"]]
