"""Structured Ingredient Parser using LLM.

This module parses ingredient text into structured JSON format with
name, quantity, unit, modifier, and prep_method fields.
"""

import json
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from lib.exceptions import LLMAPIError
from lib.llm_core import get_fast_model
from lib.logging_config import get_logger

logger = get_logger(__name__)


class IngredientParser:
    """Service for parsing ingredient text into structured format using fast LLM."""

    def __init__(self):
        """Initialize ingredient parser with fast model."""
        self.llm = get_fast_model()
        logger.debug("IngredientParser initialized with fast model")

    def parse(self, ingredient_text: str) -> Dict:
        """Parse ingredient text into structured format.

        Args:
            ingredient_text: Raw ingredient string like "2 cups fresh spinach, chopped"

        Returns:
            Dictionary with keys: name, quantity, unit, modifier, prep_method
            Example: {
                "name": "spinach",
                "quantity": 2.0,
                "unit": "cups",
                "modifier": "fresh",
                "prep_method": "chopped"
            }
        """
        prompt = f"""Parse this ingredient into structured JSON format.

Ingredient: "{ingredient_text}"

Extract the following fields:
- name: base ingredient name (lowercase)
- quantity: numeric amount (as a number, not string)
- unit: measurement unit (cups, oz, lbs, tbsp, tsp, etc.) - use null if count-based
- modifier: state modifier like "fresh", "dried", "canned", "frozen" - use null if none
- prep_method: preparation like "chopped", "diced", "minced", "sliced" - use null if none

Examples:
Input: "2 cups fresh spinach, chopped"
Output: {{"name": "spinach", "quantity": 2.0, "unit": "cups", "modifier": "fresh", "prep_method": "chopped"}}

Input: "mushrooms (16 oz)"
Output: {{"name": "mushrooms", "quantity": 16.0, "unit": "oz", "modifier": null, "prep_method": null}}

Input: "3-4 medium ripe tomatoes"
Output: {{"name": "tomatoes", "quantity": 3.5, "unit": null, "modifier": "ripe", "prep_method": null}}

Input: "fresh ginger (2-inch piece)"
Output: {{"name": "ginger", "quantity": 2.0, "unit": "inch", "modifier": "fresh", "prep_method": null}}

Respond with ONLY the JSON object, nothing else."""

        try:
            response = self.llm.generate(prompt, max_tokens=150)

            # Strip markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # Remove opening ```json or ```
                lines = response_clean.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_clean = '\n'.join(lines)

            # Parse the JSON response
            ingredient_data = json.loads(response_clean.strip())

            logger.info(
                "Parsed ingredient successfully",
                extra={"input": ingredient_text, "output": ingredient_data}
            )

            return ingredient_data

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM response as JSON: {e}",
                extra={"response": response, "ingredient": ingredient_text}
            )
            # Fallback to basic structure
            return {
                "name": ingredient_text.lower(),
                "quantity": None,
                "unit": None,
                "modifier": None,
                "prep_method": None
            }
        except LLMAPIError as e:
            logger.warning(
                f"Failed to parse ingredient with LLM: {e}",
                extra={"ingredient": ingredient_text}
            )
            # Fallback to basic structure
            return {
                "name": ingredient_text.lower(),
                "quantity": None,
                "unit": None,
                "modifier": None,
                "prep_method": None
            }

    def parse_batch(self, ingredient_texts: List[str]) -> List[Dict]:
        """Parse multiple ingredients.

        Args:
            ingredient_texts: List of raw ingredient strings

        Returns:
            List of structured ingredient dictionaries
        """
        return [self.parse(text) for text in ingredient_texts]


# Singleton instance for easy reuse
_parser_instance: Optional[IngredientParser] = None


def get_ingredient_parser() -> IngredientParser:
    """Get or create the singleton ingredient parser instance.

    Returns:
        IngredientParser instance
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IngredientParser()
    return _parser_instance


def normalize_name(name: str) -> str:
    """Normalize ingredient name for fuzzy matching.

    Args:
        name: Ingredient name

    Returns:
        Normalized name
    """
    name = name.lower().strip()

    # Simple plural removal
    if name.endswith('ies'):
        name = name[:-3] + 'y'  # berries -> berry
    elif name.endswith('es'):
        name = name[:-2]  # tomatoes -> tomat
    elif name.endswith('s') and len(name) > 3:
        name = name[:-1]  # mushrooms -> mushroom

    return name


def fuzzy_match(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """Check if two ingredient names are similar using fuzzy matching.

    Args:
        name1: First ingredient name
        name2: Second ingredient name
        threshold: Similarity threshold (0-1), default 0.85

    Returns:
        True if names are similar enough
    """
    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    # Exact match after normalization
    if norm1 == norm2:
        return True

    # Fuzzy string matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold


def find_matching_group(ingredient: Dict, groups: Dict[str, List[Dict]], threshold: float = 0.85) -> Optional[str]:
    """Find a group that matches this ingredient using fuzzy matching.

    Args:
        ingredient: Ingredient to match
        groups: Existing groups keyed by name
        threshold: Fuzzy match threshold

    Returns:
        Matching group key or None
    """
    ing_name = ingredient.get("name", "").lower()
    ing_unit = (ingredient.get("unit") or "").lower()
    ing_modifier = (ingredient.get("modifier") or "").lower()

    for group_key, group_items in groups.items():
        group_name, group_unit, group_modifier = group_key.split("::")

        # Units must match exactly
        if ing_unit != group_unit:
            continue

        # Modifiers should match (or both be empty)
        if ing_modifier != group_modifier:
            continue

        # Check fuzzy name match
        if fuzzy_match(ing_name, group_name, threshold):
            return group_key

    return None


def combine_ingredients(ingredients: List[Dict], fuzzy_threshold: float = 0.85) -> List[Dict]:
    """Combine duplicate ingredients by summing quantities with fuzzy name matching.

    Ingredients with similar names, same unit, and same modifier are combined.

    Args:
        ingredients: List of structured ingredient dictionaries
        fuzzy_threshold: Threshold for fuzzy name matching (0-1), default 0.85

    Returns:
        List of combined ingredients
    """
    # Group by fuzzy-matched (name, unit, modifier)
    # Use string key format: "name::unit::modifier"
    groups: Dict[str, List[Dict]] = {}

    for ing in ingredients:
        ing_name = ing.get("name", "").lower()
        ing_unit = (ing.get("unit") or "").lower()
        ing_modifier = (ing.get("modifier") or "").lower()

        # Try to find existing matching group
        matching_key = find_matching_group(ing, groups, fuzzy_threshold)

        if matching_key:
            # Add to existing group
            groups[matching_key].append(ing)
        else:
            # Create new group
            new_key = f"{ing_name}::{ing_unit}::{ing_modifier}"
            groups[new_key] = [ing]

    combined = []

    for group_key, group in groups.items():
        if len(group) == 1:
            # No duplicates
            combined.append(group[0])
        else:
            # Combine quantities
            total_qty = sum(
                float(ing.get("quantity", 0) or 0)
                for ing in group
            )

            # Use first item as base, update quantity
            combined_ing = group[0].copy()
            combined_ing["quantity"] = total_qty

            # Collect all prep methods
            prep_methods = [
                ing.get("prep_method")
                for ing in group
                if ing.get("prep_method")
            ]
            if prep_methods:
                # Use most common prep method
                combined_ing["prep_method"] = max(set(prep_methods), key=prep_methods.count)

            # Add note about combination
            combined_ing["from_recipes_count"] = len(group)

            combined.append(combined_ing)

    return combined


def format_ingredient(ingredient: Dict) -> str:
    """Format structured ingredient back to readable string.

    Args:
        ingredient: Structured ingredient dictionary

    Returns:
        Formatted string like "2 cups fresh spinach, chopped"
    """
    parts = []

    # Quantity and unit
    qty = ingredient.get("quantity")
    unit = ingredient.get("unit")

    if qty:
        # Format quantity nicely
        if qty == int(qty):
            parts.append(str(int(qty)))
        else:
            parts.append(f"{qty:.1f}")

    if unit:
        parts.append(unit)

    # Modifier
    modifier = ingredient.get("modifier")
    if modifier:
        parts.append(modifier)

    # Name
    name = ingredient.get("name", "")
    parts.append(name)

    # Prep method
    prep = ingredient.get("prep_method")
    if prep:
        parts.append(f"({prep})")

    return " ".join(parts)
