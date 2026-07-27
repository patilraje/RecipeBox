"""Default pantry items split into basic and optional groups."""

BASIC_PANTRY = [
    "salt",
    "black pepper",
    "water",
    "cooking oil",
]

OPTIONAL_PANTRY = [
    "paprika",
    "garlic",
    "garlic powder",
    "onion powder",
    "chilli flakes",
    "cumin",
    "oregano",
    "thyme",
    "parsley",
    "bay leaf",
    "sugar",
    "flour",
    "butter",
]


def get_pantry_defaults() -> dict[str, list[str]]:
    return {
        "basic": list(BASIC_PANTRY),
        "optional": list(OPTIONAL_PANTRY),
    }
