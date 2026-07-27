"""Ingredient normalisation: strip prep/quantities, apply synonyms."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Synonym map: variant -> canonical name
SYNONYMS: dict[str, str] = {
    "tomatoes": "tomato",
    "tomato": "tomato",
    "cherry tomatoes": "tomato",
    "roma tomatoes": "tomato",
    "tomato puree": "tomato",
    "tomato paste": "tomato",
    "tomato sauce": "tomato",
    "chopped tomatoes": "tomato",
    "tinned tomatoes": "tomato",
    "canned tomatoes": "tomato",
    "bell pepper": "bell pepper",
    "bell peppers": "bell pepper",
    "capsicum": "bell pepper",
    "red pepper": "bell pepper",
    "red peppers": "bell pepper",
    "green pepper": "bell pepper",
    "yellow pepper": "bell pepper",
    "red bell pepper": "bell pepper",
    "green bell pepper": "bell pepper",
    "yellow bell pepper": "bell pepper",
    "scallion": "green onion",
    "scallions": "green onion",
    "green onion": "green onion",
    "green onions": "green onion",
    "spring onion": "green onion",
    "spring onions": "green onion",
    "garbanzo": "chickpea",
    "garbanzos": "chickpea",
    "garbanzo bean": "chickpea",
    "garbanzo beans": "chickpea",
    "chickpea": "chickpea",
    "chickpeas": "chickpea",
    "chilli": "chili",
    "chillies": "chili",
    "chilies": "chili",
    "chili": "chili",
    "chili flakes": "chilli flakes",
    "chilli flakes": "chilli flakes",
    "red pepper flakes": "chilli flakes",
    "chili powder": "chili",
    "chilli powder": "chili",
    "chicken": "chicken",
    "chicken breasts": "chicken",
    "chicken breast": "chicken",
    "chicken thighs": "chicken",
    "chicken thigh": "chicken",
    "chicken legs": "chicken",
    "chicken stock": "chicken stock",
    "chicken stock cube": "chicken stock",
    "eggs": "egg",
    "egg": "egg",
    "onions": "onion",
    "onion": "onion",
    "red onion": "onion",
    "yellow onion": "onion",
    "white onion": "onion",
    "cooking oil": "cooking oil",
    "vegetable oil": "cooking oil",
    "olive oil": "cooking oil",
    "sunflower oil": "cooking oil",
    "oil": "cooking oil",
    "black pepper": "black pepper",
    "pepper": "black pepper",
    "ground black pepper": "black pepper",
    "ground pepper": "black pepper",
    "kosher salt": "salt",
    "sea salt": "salt",
    "table salt": "salt",
    "salt": "salt",
    "garlic cloves": "garlic",
    "garlic clove": "garlic",
    "cloves garlic": "garlic",
    "minced garlic": "garlic",
    "garlic": "garlic",
    "fresh thyme": "thyme",
    "thyme": "thyme",
    "fresh parsley": "parsley",
    "parsley": "parsley",
    "bay leaves": "bay leaf",
    "bay leaf": "bay leaf",
    "potatoes": "potato",
    "potato": "potato",
    "sweet potatoes": "sweet potato",
    "sweet potato": "sweet potato",
    "carrots": "carrot",
    "carrot": "carrot",
    "mushrooms": "mushroom",
    "mushroom": "mushroom",
    "cheddar cheese": "cheese",
    "mozzarella": "cheese",
    "mozzarella cheese": "cheese",
    "parmesan": "cheese",
    "parmesan cheese": "cheese",
    "cheese": "cheese",
    "basmati rice": "rice",
    "jasmine rice": "rice",
    "white rice": "rice",
    "brown rice": "rice",
    "rice": "rice",
    "ground beef": "beef",
    "beef mince": "beef",
    "minced beef": "beef",
    "beef": "beef",
    "prawns": "shrimp",
    "shrimp": "shrimp",
    "courgette": "zucchini",
    "courgettes": "zucchini",
    "zucchini": "zucchini",
    "zucchinis": "zucchini",
    "coriander": "cilantro",
    "fresh coriander": "cilantro",
    "cilantro": "cilantro",
    "aubergine": "eggplant",
    "eggplants": "eggplant",
    "eggplant": "eggplant",
    "minced meat": "beef",
    "all-purpose flour": "flour",
    "plain flour": "flour",
    "flour": "flour",
    "unsalted butter": "butter",
    "salted butter": "butter",
    "butter": "butter",
    "caster sugar": "sugar",
    "white sugar": "sugar",
    "granulated sugar": "sugar",
    "sugar": "sugar",
    "garlic powder": "garlic powder",
    "onion powder": "onion powder",
    "paprika": "paprika",
    "cumin": "cumin",
    "ground cumin": "cumin",
    "cumin seeds": "cumin",
    "oregano": "oregano",
    "dried oregano": "oregano",
    "water": "water",
}

UNITS = {
    "g",
    "kg",
    "mg",
    "ml",
    "l",
    "oz",
    "lb",
    "lbs",
    "tsp",
    "tbsp",
    "teaspoon",
    "teaspoons",
    "tablespoon",
    "tablespoons",
    "cup",
    "cups",
    "pint",
    "pints",
    "quart",
    "quarts",
    "gallon",
    "gallons",
    "clove",
    "cloves",
    "slice",
    "slices",
    "piece",
    "pieces",
    "pinch",
    "pinches",
    "dash",
    "handful",
    "can",
    "cans",
    "package",
    "packages",
    "bunch",
    "bunches",
}

PREP_WORDS = {
    "finely",
    "roughly",
    "freshly",
    "thinly",
    "thickly",
    "lightly",
    "chopped",
    "diced",
    "minced",
    "sliced",
    "grated",
    "shredded",
    "crushed",
    "peeled",
    "seeded",
    "deseeded",
    "halved",
    "quartered",
    "cubed",
    "melted",
    "softened",
    "beaten",
    "whisked",
    "drained",
    "rinsed",
    "cooked",
    "uncooked",
    "raw",
    "fresh",
    "dried",
    "frozen",
    "canned",
    "whole",
    "large",
    "medium",
    "small",
    "extra",
    "virgin",
    "optional",
    "to",
    "taste",
    "for",
    "serving",
    "garnish",
    "and",
    "or",
    "of",
    "a",
    "an",
    "the",
    "into",
    "cut",
    "stripped",
    "trimmed",
    "boneless",
    "skinless",
}


@dataclass
class NormalisedIngredient:
    original: str
    canonical_name: str
    quantity: float | None = None
    unit: str | None = None
    preparation: str | None = None


WORD_NUMBERS = {
    "a": 1.0,
    "an": 1.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "dozen": 12.0,
}

_QUANTITY_RE = re.compile(
    r"^("
    r"\d+\s*/\s*\d+"  # fractions like 1/2
    r"|\d+\.\d+"
    r"|\d+"
    r"|½|⅓|⅔|¼|¾"
    r")"
    r"(\s*-\s*("
    r"\d+\s*/\s*\d+|\d+\.\d+|\d+|½|⅓|⅔|¼|¾"
    r"))?"
)


def _strip_punctuation(text: str) -> str:
    return re.sub(r"[^\w\s/-]", " ", text)


def _extract_quantity_and_unit(tokens: list[str]) -> tuple[float | None, str | None, list[str]]:
    if not tokens:
        return None, None, tokens

    quantity: float | None = None
    unit: str | None = None
    rest = list(tokens)

    first = rest[0].lower()
    match = _QUANTITY_RE.match(rest[0])
    if match or rest[0] in {"½", "⅓", "⅔", "¼", "¾"}:
        raw = rest.pop(0)
        fraction_map = {"½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75}
        try:
            if "/" in raw:
                num, den = raw.split("/")
                quantity = float(num.strip()) / float(den.strip())
            elif raw in fraction_map:
                quantity = fraction_map[raw]
            else:
                quantity = float(raw)
        except ValueError:
            rest.insert(0, raw)
            quantity = None
    elif first in WORD_NUMBERS:
        quantity = WORD_NUMBERS[first]
        rest.pop(0)

    if rest and rest[0].lower() in UNITS:
        unit = rest.pop(0).lower()

    # Handle glued forms like "250g"
    if quantity is None and rest:
        glued = re.match(r"^(\d+(?:\.\d+)?)([a-zA-Z]+)$", rest[0])
        if glued and glued.group(2).lower() in UNITS:
            quantity = float(glued.group(1))
            unit = glued.group(2).lower()
            rest.pop(0)

    return quantity, unit, rest


def _apply_synonym(name: str) -> str:
    if name in SYNONYMS:
        return SYNONYMS[name]
    # Try without trailing s
    if name.endswith("ies") and name[:-3] + "y" in SYNONYMS:
        return SYNONYMS[name[:-3] + "y"]
    if name.endswith("es") and name[:-2] in SYNONYMS:
        return SYNONYMS[name[:-2]]
    if name.endswith("s") and name[:-1] in SYNONYMS:
        return SYNONYMS[name[:-1]]
    return name


def normalize_ingredient(raw: str) -> NormalisedIngredient:
    original = raw.strip()
    text = _strip_punctuation(original.lower())
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    quantity, unit, tokens = _extract_quantity_and_unit(tokens)

    prep_tokens = [t for t in tokens if t in PREP_WORDS]
    name_tokens = [t for t in tokens if t not in PREP_WORDS and t not in UNITS]

    # If everything was stripped as prep, fall back to full token list
    if not name_tokens:
        name_tokens = [t for t in tokens if t not in UNITS]

    canonical = " ".join(name_tokens).strip()
    canonical = _apply_synonym(canonical)

    # Longer phrase synonyms already handled; also try last 1–3 tokens
    if canonical not in SYNONYMS.values():
        for n in (3, 2, 1):
            if len(name_tokens) >= n:
                phrase = " ".join(name_tokens[-n:])
                mapped = _apply_synonym(phrase)
                if mapped != phrase or phrase in SYNONYMS:
                    canonical = mapped
                    break

    preparation = " ".join(prep_tokens) if prep_tokens else None

    return NormalisedIngredient(
        original=original,
        canonical_name=canonical or original.lower().strip(),
        quantity=quantity,
        unit=unit,
        preparation=preparation,
    )


def normalize_many(ingredients: list[str]) -> list[NormalisedIngredient]:
    return [normalize_ingredient(item) for item in ingredients if item and item.strip()]


def canonicalize_query_terms(ingredients: list[str]) -> list[str]:
    """Return unique canonical names suitable for MealDB filter queries."""
    seen: list[str] = []
    for item in normalize_many(ingredients):
        name = item.canonical_name
        if name and name not in seen:
            seen.append(name)
    return seen


def canonical_set(ingredients: list[str]) -> set[str]:
    return {n.canonical_name for n in normalize_many(ingredients) if n.canonical_name}
