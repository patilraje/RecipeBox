"""Recipe generation: Gemini (Google AI Studio) → Groq → templates.

Set GOOGLE_API_KEY from https://aistudio.google.com/apikey
Optional: GROQ_API_KEY as backup
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Literal

import httpx

from app.config import settings
from app.matcher import MatchType, contains_excluded, match_recipe
from app.normalizer import canonical_set

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
Provider = Literal["gemini", "groq", "ollama", "template"]

RECIPE_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": "string"},
                },
                "required": ["name", "amount"],
                "additionalProperties": False,
            },
        },
        "instructions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "cooking_time_minutes": {"type": "integer"},
        "servings": {"type": "integer"},
    },
    "required": [
        "title",
        "ingredients",
        "instructions",
        "cooking_time_minutes",
        "servings",
    ],
    "additionalProperties": False,
}

BATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "recipes": {
            "type": "array",
            "items": RECIPE_ITEM_SCHEMA,
        }
    },
    "required": ["recipes"],
    "additionalProperties": False,
}

# --- lightweight template fallback (no API key) ---

PROTEINS = {
    "chicken", "chicken breast", "chicken thigh", "beef", "pork", "lamb",
    "shrimp", "fish", "salmon", "egg", "tofu", "chickpea", "bean", "lentil",
}
STARCHES = {
    "rice", "potato", "sweet potato", "pasta", "noodle", "bread", "flour",
    "quinoa", "couscous",
}
VEGETABLES = {
    "tomato", "onion", "bell pepper", "garlic", "carrot", "mushroom",
    "zucchini", "eggplant", "spinach", "broccoli", "cabbage", "green onion",
    "celery", "corn", "pea", "cucumber", "lettuce", "cilantro", "parsley",
}
DAIRY = {"cheese", "butter", "milk", "cream", "yogurt"}
STAPLES = {"salt", "black pepper", "cooking oil", "water"}


def _pick_group(canonical: set[str], group: set[str]) -> list[str]:
    return sorted(canonical & group)


def _amount_for(name: str, servings: int) -> str:
    if name in PROTEINS:
        return f"{150 * servings} g"
    if name == "rice":
        return f"{80 * servings} g"
    if name in STARCHES:
        return f"{100 * servings} g"
    if name == "egg":
        return f"{servings + 1}"
    if name in {"onion", "tomato", "bell pepper"}:
        return f"{max(1, servings // 2 + 1)}"
    if name in VEGETABLES:
        return f"{80 * servings} g"
    if name == "cheese":
        return f"{40 * servings} g"
    if name in {"salt", "black pepper"}:
        return "to taste"
    if name == "cooking oil":
        return "1–2 tbsp"
    if name == "water":
        return f"{150 * servings} ml"
    if name in {
        "paprika", "cumin", "oregano", "thyme", "chilli flakes",
        "garlic powder", "onion powder", "garlic", "parsley",
    }:
        return "1 tsp"
    return "as needed"


def _template_subset(
    user: set[str],
    pantry: set[str],
    excluded: set[str],
    index: int,
    count: int,
) -> list[str]:
    """Pick a focused subset so each fallback recipe differs."""
    allowed = (user | pantry) - excluded
    proteins = _pick_group(user - excluded, PROTEINS) or _pick_group(allowed, PROTEINS)
    starches = _pick_group(user - excluded, STARCHES) or _pick_group(allowed, STARCHES)
    veg = _pick_group(user - excluded, VEGETABLES) or _pick_group(allowed, VEGETABLES)
    dairy = _pick_group(user - excluded, DAIRY)

    # Rotate focus across recipes
    p = proteins[index % len(proteins)] if proteins else None
    s = starches[(index // max(1, len(proteins) or 1)) % len(starches)] if starches else None
    v_start = index % max(1, len(veg) or 1)
    vs = veg[v_start : v_start + 2] if veg else []
    if not vs and veg:
        vs = [veg[index % len(veg)]]

    core = [x for x in [p, s, *vs] if x]
    if dairy and index % 2 == 0:
        core.append(dairy[0])
    if not core:
        core = sorted(user - excluded)[: 3 + (index % 3)] or sorted(allowed)[:4]

    spices = sorted(
        (pantry & allowed)
        - STAPLES
        - {"butter", "flour", "sugar"}
    )
    spice = [spices[index % len(spices)]] if spices else []
    staples = sorted(STAPLES & allowed & pantry)
    return list(dict.fromkeys([*core, *spice, *staples]))


def _template_recipe(
    names: list[str],
    servings: int,
    index: int,
) -> dict[str, Any]:
    proteins = [n for n in names if n in PROTEINS]
    starches = [n for n in names if n in STARCHES]
    vegetables = [n for n in names if n in VEGETABLES]
    spices = [
        n for n in names
        if n not in PROTEINS | STARCHES | VEGETABLES | DAIRY | STAPLES
    ]
    title_bits = []
    if spices:
        title_bits.append(spices[0].title())
    if proteins:
        title_bits.append(proteins[0].title())
    if vegetables:
        title_bits.append(f"and {vegetables[0].title()}")
    if starches:
        title_bits.append(starches[0].title())
    title = " ".join(title_bits) or f"Pantry Meal {index + 1}"

    steps = []
    if "rice" in starches:
        steps.append("Rinse the rice and simmer in water until tender.")
    if "cooking oil" in names:
        steps.append("Heat cooking oil in a pan over medium heat.")
    if proteins:
        steps.append(f"Cook the {proteins[0]} until done.")
    if vegetables:
        steps.append(f"Add {', '.join(vegetables)} and cook until softened.")
    if spices or "salt" in names:
        season = ", ".join([*(spices[:2]), *[s for s in ("salt", "black pepper") if s in names]])
        if season:
            steps.append(f"Season with {season}.")
    steps.append(f"Serve hot for {servings}.")

    return {
        "title": title,
        "ingredients": [{"name": n, "amount": _amount_for(n, servings)} for n in names],
        "instructions": steps,
        "cooking_time_minutes": 20 + 5 * len([n for n in names if n not in STAPLES]),
        "servings": servings,
    }


def _build_prompt(
    user_ingredients: list[str],
    pantry_defaults: list[str],
    exclude_ingredients: list[str],
    diet: str | None,
    servings: int,
    count: int,
) -> str:
    user_lines = "\n".join(f"- {i}" for i in sorted(canonical_set(user_ingredients)))
    pantry_lines = "\n".join(f"- {i}" for i in sorted(canonical_set(pantry_defaults)))
    exclude_lines = (
        "\n".join(f"- {i}" for i in sorted(canonical_set(exclude_ingredients)))
        if exclude_ingredients
        else "- (none)"
    )
    return f"""Create exactly {count} DIFFERENT recipes.

Available ingredients (main foods):
{user_lines}

Allowed pantry staples/spices:
{pantry_lines}

Do not use these excluded ingredients:
{exclude_lines}

Diet preference: {diet or "none"}
Servings per recipe: {servings}

Rules:
- Each recipe must be distinct in style, method, and ingredient focus.
- Do NOT put every available ingredient into every recipe.
- Each recipe should use a sensible subset (typically 3–7 food items plus a few pantry staples).
- Different recipes should emphasize different proteins/vegetables/starches when possible.
- Ingredient names must come ONLY from the available + pantry lists above (use those exact names).
- No garnishes, sauces, or extras not on the lists.
- Clear step-by-step instructions.
- Realistic cooking times.
"""


class AIRecipeGenerator:
    def __init__(self) -> None:
        self.last_provider: Provider = "template"

    @property
    def configured(self) -> bool:
        return True

    @property
    def uses_llm(self) -> bool:
        return bool(settings.google_api_key or settings.groq_api_key)

    def _to_card(
        self,
        data: dict[str, Any],
        *,
        user_ingredients: list[str],
        pantry_defaults: list[str],
    ) -> dict[str, Any]:
        names = [item["name"] for item in data.get("ingredients", [])]
        match = match_recipe(names, user_ingredients, pantry_defaults, maximum_missing=0)
        return {
            "id": f"ai-{uuid.uuid4().hex[:12]}",
            "name": data.get("title") or "Generated Recipe",
            "image_url": None,
            "cooking_time_minutes": data.get("cooking_time_minutes"),
            "servings": data.get("servings"),
            "ingredients": names,
            "ingredients_detailed": [
                {"name": i["name"], "amount": i.get("amount")}
                for i in data.get("ingredients", [])
            ],
            "ingredients_used": match.ingredients_used,
            "pantry_spices_used": match.pantry_spices_used,
            "missing_ingredients": match.missing_ingredients,
            "instructions": data.get("instructions") or [],
            "source": "ai",
            "source_url": None,
            "match_type": "ai_created",
        }

    def _is_valid(
        self,
        data: dict[str, Any],
        user_ingredients: list[str],
        pantry_defaults: list[str],
        exclude_ingredients: list[str],
    ) -> bool:
        names = [item["name"] for item in data.get("ingredients", [])]
        if not names:
            return False
        if contains_excluded(names, exclude_ingredients):
            return False
        match = match_recipe(names, user_ingredients, pantry_defaults, maximum_missing=0)
        return match.result_type == MatchType.EXACT

    def _parse_recipes(self, content: str, count: int) -> list[dict[str, Any]]:
        text = content.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        parsed = json.loads(text)
        recipes = parsed.get("recipes") if isinstance(parsed, dict) else parsed
        if not isinstance(recipes, list):
            raise ValueError("LLM response missing recipes list")
        return recipes[:count]

    async def _call_gemini(self, prompt: str, count: int) -> list[dict[str, Any]]:
        model = settings.gemini_model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        body = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a creative home cook. Invent distinct, practical recipes. "
                            "Never invent ingredients outside the allowed lists. "
                            "Respond with JSON only."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                            + f"\n\nReturn exactly {count} recipes as JSON with this shape:\n"
                            '{"recipes":[{"title":"...","ingredients":[{"name":"...","amount":"..."}],'
                            '"instructions":["..."],"cooking_time_minutes":30,"servings":2}]}'
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.85,
                "responseMimeType": "application/json",
            },
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                url,
                params={"key": settings.google_api_key},
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
        parts = payload["candidates"][0]["content"]["parts"]
        content = "".join(p.get("text", "") for p in parts)
        return self._parse_recipes(content, count)

    async def _call_groq(self, prompt: str, count: int) -> list[dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": settings.groq_model,
            "temperature": 0.85,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a creative home cook. Invent distinct, practical recipes. "
                        "Never invent ingredients outside the allowed lists. "
                        "Respond with JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "recipes_batch",
                    "schema": BATCH_SCHEMA,
                },
            },
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(GROQ_URL, headers=headers, json=body)
            if response.status_code >= 400:
                body["response_format"] = {"type": "json_object"}
                body["messages"][-1]["content"] = (
                    prompt
                    + f'\n\nReturn JSON: {{"recipes":[...]}} with exactly {count} recipes.'
                )
                response = await client.post(GROQ_URL, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
        content = payload["choices"][0]["message"]["content"] or "{}"
        return self._parse_recipes(content, count)

    def _template_batch(
        self,
        user_ingredients: list[str],
        pantry_defaults: list[str],
        exclude_ingredients: list[str],
        servings: int,
        count: int,
    ) -> list[dict[str, Any]]:
        user = canonical_set(user_ingredients)
        pantry = canonical_set(pantry_defaults)
        excluded = canonical_set(exclude_ingredients)
        out: list[dict[str, Any]] = []
        for i in range(count):
            names = _template_subset(user, pantry, excluded, i, count)
            out.append(_template_recipe(names, servings, i))
        return out

    async def _llm_batch(
        self, prompt: str, count: int
    ) -> tuple[list[dict[str, Any]], Provider]:
        if settings.google_api_key:
            try:
                return await self._call_gemini(prompt, count), "gemini"
            except Exception:
                try:
                    return await self._call_gemini(
                        prompt
                        + "\n\nUse ONLY listed ingredient names; fewer ingredients per recipe.",
                        count,
                    ), "gemini"
                except Exception:
                    pass
        if settings.groq_api_key:
            try:
                return await self._call_groq(prompt, count), "groq"
            except Exception:
                pass
        return [], "template"

    async def generate_many(
        self,
        user_ingredients: list[str],
        pantry_defaults: list[str],
        exclude_ingredients: list[str] | None = None,
        diet: str | None = None,
        servings: int = 2,
        count: int = 1,
    ) -> list[dict[str, Any]]:
        count = max(1, min(8, count))
        exclude_ingredients = list(exclude_ingredients or [])
        prompt = _build_prompt(
            user_ingredients,
            pantry_defaults,
            exclude_ingredients,
            diet,
            servings,
            count,
        )
        recipes_raw, provider = await self._llm_batch(prompt, count)
        if not recipes_raw:
            recipes_raw = self._template_batch(
                user_ingredients,
                pantry_defaults,
                exclude_ingredients,
                servings,
                count,
            )
            provider = "template"
        self.last_provider = provider

        cards: list[dict[str, Any]] = []
        for data in recipes_raw:
            if not self._is_valid(
                data, user_ingredients, pantry_defaults, exclude_ingredients
            ):
                continue
            cards.append(
                self._to_card(
                    data,
                    user_ingredients=user_ingredients,
                    pantry_defaults=pantry_defaults,
                )
            )

        if len(cards) < count:
            fillers = self._template_batch(
                user_ingredients,
                pantry_defaults,
                exclude_ingredients,
                servings,
                count,
            )
            for data in fillers:
                if len(cards) >= count:
                    break
                if not self._is_valid(
                    data, user_ingredients, pantry_defaults, exclude_ingredients
                ):
                    continue
                card = self._to_card(
                    data,
                    user_ingredients=user_ingredients,
                    pantry_defaults=pantry_defaults,
                )
                if any(c["name"] == card["name"] for c in cards):
                    card["name"] = f"{card['name']} ({len(cards) + 1})"
                cards.append(card)

        if not cards:
            raise ValueError("Could not generate valid recipes from the allowed ingredients.")
        return cards[:count]

    async def generate(
        self,
        user_ingredients: list[str],
        pantry_defaults: list[str],
        exclude_ingredients: list[str] | None = None,
        diet: str | None = None,
        servings: int = 2,
    ) -> dict[str, Any]:
        cards = await self.generate_many(
            user_ingredients,
            pantry_defaults,
            exclude_ingredients=exclude_ingredients,
            diet=diet,
            servings=servings,
            count=1,
        )
        return cards[0]
