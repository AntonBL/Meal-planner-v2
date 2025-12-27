"""Unified Ingredient Schema and Conversion Utilities.

This module defines the canonical ingredient format used throughout the application
and provides functions to convert between different formats.

CANONICAL FORMAT:
-----------------
Recipes should store ingredients as a list of objects with this structure:

{
    "ingredients": [
        {
            "item": "2 cups fresh spinach",
            "name": "spinach",
            "quantity": "2",
            "unit": "cups",
            "modifier": "fresh",
            "status": "available"  // or "needed"
        },
        {
            "item": "1 lb tomatoes",
            "name": "tomatoes",
            "quantity": "1",
            "unit": "lb",
            "modifier": null,
            "status": "needed"
        }
    ]
}

LEGACY FORMATS SUPPORTED:
-------------------------
1. Simple string list: ["2 cups spinach", "1 onion"]
2. Comma-separated strings in ingredients_available/ingredients_needed
3. Structured shopping list format

"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# CANONICAL INGREDIENT SCHEMA
# ============================================================================

def create_ingredient(
    item: str,
    name: str = None,
    quantity: str = None,
    unit: str = None,
    modifier: str = None,
    status: str = "needed"
) -> dict:
    """Create an ingredient in the canonical format.

    Args:
        item: Full ingredient text (e.g., "2 cups fresh spinach")
        name: Ingredient name (e.g., "spinach")
        quantity: Amount (e.g., "2")
        unit: Unit of measure (e.g., "cups")
        modifier: Descriptor (e.g., "fresh", "diced")
        status: "available" or "needed" (default: "needed")

    Returns:
        Ingredient dictionary in canonical format

    Example:
        >>> create_ingredient("2 cups fresh spinach", "spinach", "2", "cups", "fresh", "available")
        {
            "item": "2 cups fresh spinach",
            "name": "spinach",
            "quantity": "2",
            "unit": "cups",
            "modifier": "fresh",
            "status": "available"
        }
    """
    return {
        "item": item.strip(),
        "name": name.strip().lower() if name else item.strip().lower(),
        "quantity": quantity.strip() if quantity else None,
        "unit": unit.strip().lower() if unit else None,
        "modifier": modifier.strip() if modifier else None,
        "status": status if status in ["available", "needed"] else "needed"
    }


# ============================================================================
# CONVERSION FROM LEGACY FORMATS
# ============================================================================

def from_string_list(ingredients: list[str], status: str = "needed") -> list[dict]:
    """Convert legacy string list to canonical format.

    Args:
        ingredients: List of ingredient strings (e.g., ["2 cups spinach", "1 onion"])
        status: Default status for all ingredients ("available" or "needed")

    Returns:
        List of ingredients in canonical format

    Example:
        >>> from_string_list(["2 cups spinach", "1 onion"], "available")
        [
            {"item": "2 cups spinach", "name": "spinach", ...},
            {"item": "1 onion", "name": "onion", ...}
        ]
    """
    if not ingredients or not isinstance(ingredients, list):
        return []

    canonical = []
    for ing in ingredients:
        if not ing or not isinstance(ing, str):
            continue

        # Try to parse using ingredient parser if available
        try:
            from lib.ingredient_parser import parse_ingredient
            parsed = parse_ingredient(ing)
            canonical.append({
                "item": ing.strip(),
                "name": parsed.get("name", ing.strip().lower()),
                "quantity": str(parsed.get("quantity")) if parsed.get("quantity") else None,
                "unit": parsed.get("unit"),
                "modifier": parsed.get("modifier"),
                "status": status
            })
        except Exception as e:
            logger.debug(f"Parser not available or failed for '{ing}': {e}")
            # Fallback: minimal structure
            canonical.append({
                "item": ing.strip(),
                "name": ing.strip().lower(),
                "quantity": None,
                "unit": None,
                "modifier": None,
                "status": status
            })

    return canonical


def from_comma_separated(
    ingredients_available: str = None,
    ingredients_needed: str = None
) -> list[dict]:
    """Convert legacy comma-separated strings to canonical format.

    Args:
        ingredients_available: Comma-separated string of available ingredients
        ingredients_needed: Comma-separated string of needed ingredients

    Returns:
        Combined list of ingredients in canonical format

    Example:
        >>> from_comma_separated("oil, salt", "3 tomatoes, basil")
        [
            {"item": "oil", "status": "available", ...},
            {"item": "salt", "status": "available", ...},
            {"item": "3 tomatoes", "status": "needed", ...},
            {"item": "basil", "status": "needed", ...}
        ]
    """
    canonical = []

    if ingredients_available:
        available_list = [i.strip() for i in ingredients_available.split(',') if i.strip()]
        canonical.extend(from_string_list(available_list, status="available"))

    if ingredients_needed:
        needed_list = [i.strip() for i in ingredients_needed.split(',') if i.strip()]
        canonical.extend(from_string_list(needed_list, status="needed"))

    return canonical


def from_legacy_recipe(recipe: dict) -> list[dict]:
    """Convert a recipe with any legacy ingredient format to canonical format.

    Handles multiple legacy formats:
    - Simple list: recipe["ingredients"] = ["2 cups spinach", ...]
    - Comma-separated: recipe["ingredients_available"], recipe["ingredients_needed"]
    - Mixed formats

    Args:
        recipe: Recipe dictionary with ingredients in any format

    Returns:
        List of ingredients in canonical format, or empty list if none found

    Example:
        >>> recipe = {"ingredients_available": "oil", "ingredients_needed": "tomatoes"}
        >>> from_legacy_recipe(recipe)
        [{"item": "oil", "status": "available", ...}, ...]
    """
    # Priority 1: Check if already in canonical format
    ingredients = recipe.get("ingredients", [])
    if ingredients and isinstance(ingredients, list) and len(ingredients) > 0:
        # Check if first item is already in canonical format
        if isinstance(ingredients[0], dict) and "status" in ingredients[0]:
            return ingredients

    # Priority 2: Use comma-separated strings if available
    if recipe.get("ingredients_available") or recipe.get("ingredients_needed"):
        return from_comma_separated(
            recipe.get("ingredients_available"),
            recipe.get("ingredients_needed")
        )

    # Priority 3: Convert simple string list (assume all needed)
    if ingredients and isinstance(ingredients, list):
        return from_string_list(ingredients, status="needed")

    # No ingredients found
    logger.warning(f"No ingredients found in recipe: {recipe.get('name', 'unknown')}")
    return []


# ============================================================================
# CONVERSION TO OUTPUT FORMATS
# ============================================================================

def to_string_list(ingredients: list[dict]) -> list[str]:
    """Convert canonical format to simple string list.

    Args:
        ingredients: List of ingredients in canonical format

    Returns:
        List of ingredient strings

    Example:
        >>> to_string_list([{"item": "2 cups spinach", ...}])
        ["2 cups spinach"]
    """
    if not ingredients:
        return []

    return [ing.get("item", "") for ing in ingredients if ing.get("item")]


def to_comma_separated(
    ingredients: list[dict],
    status_filter: str = None
) -> str:
    """Convert canonical format to comma-separated string.

    Args:
        ingredients: List of ingredients in canonical format
        status_filter: Only include ingredients with this status (None = all)

    Returns:
        Comma-separated string

    Example:
        >>> ings = [{"item": "oil", "status": "available"}, {"item": "salt", "status": "needed"}]
        >>> to_comma_separated(ings, "available")
        "oil"
    """
    if not ingredients:
        return ""

    filtered = ingredients
    if status_filter:
        filtered = [ing for ing in ingredients if ing.get("status") == status_filter]

    return ", ".join([ing.get("item", "") for ing in filtered if ing.get("item")])


def split_by_status(ingredients: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split ingredients into available and needed lists.

    Args:
        ingredients: List of ingredients in canonical format

    Returns:
        Tuple of (available_ingredients, needed_ingredients)

    Example:
        >>> ings = [{"item": "oil", "status": "available"}, {"item": "salt", "status": "needed"}]
        >>> available, needed = split_by_status(ings)
        >>> len(available), len(needed)
        (1, 1)
    """
    available = [ing for ing in ingredients if ing.get("status") == "available"]
    needed = [ing for ing in ingredients if ing.get("status") == "needed"]
    return available, needed


# ============================================================================
# VALIDATION
# ============================================================================

def validate_ingredient(ingredient: Any) -> bool:
    """Validate that an ingredient matches the canonical format.

    Args:
        ingredient: Ingredient to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_ingredient({"item": "salt", "name": "salt", "status": "needed"})
        True
        >>> validate_ingredient("salt")
        False
    """
    if not isinstance(ingredient, dict):
        return False

    required_fields = ["item", "name", "status"]
    for field in required_fields:
        if field not in ingredient:
            return False

    if ingredient["status"] not in ["available", "needed"]:
        return False

    return True


def validate_ingredients_list(ingredients: Any) -> bool:
    """Validate that a list of ingredients matches the canonical format.

    Args:
        ingredients: List to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(ingredients, list):
        return False

    if len(ingredients) == 0:
        return True  # Empty list is valid

    return all(validate_ingredient(ing) for ing in ingredients)


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def get_display_text(ingredient: dict) -> str:
    """Get formatted display text for an ingredient.

    Args:
        ingredient: Ingredient in canonical format

    Returns:
        Formatted string for display

    Example:
        >>> get_display_text({"item": "2 cups spinach", "status": "available"})
        "✓ 2 cups spinach"
    """
    item = ingredient.get("item", "Unknown ingredient")
    status = ingredient.get("status", "needed")

    prefix = "✓ " if status == "available" else "○ "
    return f"{prefix}{item}"


def summary_text(ingredients: list[dict]) -> str:
    """Get a summary of ingredients by status.

    Args:
        ingredients: List of ingredients in canonical format

    Returns:
        Summary string

    Example:
        >>> ings = [{"status": "available"}, {"status": "available"}, {"status": "needed"}]
        >>> summary_text(ings)
        "3 ingredients (2 available, 1 needed)"
    """
    if not ingredients:
        return "No ingredients"

    available, needed = split_by_status(ingredients)
    total = len(ingredients)

    return f"{total} ingredient{'s' if total != 1 else ''} ({len(available)} available, {len(needed)} needed)"
