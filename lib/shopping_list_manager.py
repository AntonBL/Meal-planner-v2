"""Shopping List Management Functions.

Shared functions for managing the shopping list using JSON storage.
Supports structured ingredients with automatic parsing and combination.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from lib.ingredient_parser import (
    get_ingredient_parser,
    combine_ingredients,
    format_ingredient,
    fuzzy_match
)
from lib.logging_config import get_logger

logger = get_logger(__name__)


def _get_shopping_list_path() -> Path:
    """Get the path to the shopping list JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "shopping_list.json"


def _load_list_data() -> dict:
    """Load the full shopping list data structure from JSON."""
    list_path = _get_shopping_list_path()
    if not list_path.exists():
        return {"items": [], "last_updated": None}
    
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse shopping list JSON: {e}")
        return {"items": [], "last_updated": None}


def _save_list_data(data: dict) -> bool:
    """Save the full shopping list data structure to JSON."""
    try:
        list_path = _get_shopping_list_path()
        data["last_updated"] = datetime.now().isoformat()
        
        with open(list_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save shopping list JSON: {e}")
        return False




def categorize_ingredient(ingredient_name: str) -> str:
    """Categorize an ingredient using LLM for shopping list organization.
    
    Args:
        ingredient_name: Name of the ingredient
        
    Returns:
        Category name
    """
    from lib.ingredient_agent import get_ingredient_categorizer
    
    try:
        categorizer = get_ingredient_categorizer()
        return categorizer.categorize(ingredient_name)
    except Exception as e:
        logger.warning(f"Failed to categorize ingredient with LLM: {e}")
        # Fallback to simple default
        return "Other"


def _ensure_structured_data(items: List[Dict]) -> List[Dict]:
    """Ensure all items have structured data by parsing if needed.

    Args:
        items: List of shopping list items

    Returns:
        List of items with structured data added
    """
    parser = get_ingredient_parser()
    modified = False

    for item in items:
        if 'structured' not in item or not item.get('structured'):
            # Parse the item text to add structured data
            try:
                item['structured'] = parser.parse(item['item'])
                modified = True
                logger.info(f"Migrated item to structured format: {item['item']}")
            except Exception as e:
                logger.warning(f"Failed to parse item {item['item']}: {e}")
                # Add minimal structured data
                item['structured'] = {
                    "name": item['item'].lower(),
                    "quantity": None,
                    "unit": None,
                    "modifier": None,
                    "prep_method": None
                }

    return items, modified


def load_shopping_list() -> List[Dict]:
    """Load the current shopping list items.

    Returns:
        List of item dictionaries
    """
    data = _load_list_data()
    items = data.get("items", [])

    # Ensure all items have structured data (migrate old format)
    items, modified = _ensure_structured_data(items)

    # Save if we modified anything
    if modified:
        data["items"] = items
        _save_list_data(data)

    return items


def is_recipe_in_shopping_list(recipe_name: str) -> bool:
    """Check if a recipe's ingredients are in the shopping list.

    Args:
        recipe_name: Name of the recipe

    Returns:
        True if the recipe has any items in the shopping list, False otherwise
    """
    try:
        items = load_shopping_list()
        return any(item.get('recipe') == recipe_name for item in items)
    except Exception as e:
        logger.error(f"Failed to check if recipe in shopping list: {e}", exc_info=True)
        return False


def add_items_to_list(recipe_name: str, ingredients: List[str]) -> bool:
    """Add ingredients for a recipe to the shopping list with automatic parsing.

    Ingredients are parsed into structured format (name, quantity, unit, etc.)
    for better combination and organization.

    Args:
        recipe_name: Name of the recipe
        ingredients: List of ingredient strings

    Returns:
        True if successful, False otherwise
    """
    try:
        if not ingredients:
            return True

        data = _load_list_data()
        items = data.get("items", [])
        today = datetime.now().strftime("%Y-%m-%d")

        # Parse ingredients into structured format
        parser = get_ingredient_parser()

        count = 0
        for ing_text in ingredients:
            ing_text = ing_text.strip()
            if not ing_text:
                continue

            # Parse the ingredient
            parsed = parser.parse(ing_text)
            parsed_name = parsed.get("name", "").lower()
            parsed_unit = (parsed.get("unit") or "").lower()

            # Get category for this ingredient
            category = categorize_ingredient(parsed.get("name", ing_text))

            # Check for duplicates using fuzzy matching (same as combination logic)
            # Two ingredients are duplicates if:
            # 1. They're for the same recipe
            # 2. They have matching names (fuzzy match)
            # 3. They have the same unit (to avoid mixing counts and volumes)
            duplicate_item = None
            for item in items:
                if item.get('recipe') != recipe_name:
                    continue
                if 'structured' not in item:
                    continue

                existing_name = item.get('structured', {}).get('name', '').lower()
                existing_unit = (item.get('structured', {}).get('unit') or '').lower()

                # Must have matching units (or both empty)
                if existing_unit != parsed_unit:
                    continue

                # Check fuzzy name match
                if fuzzy_match(existing_name, parsed_name):
                    duplicate_item = item
                    break

            if duplicate_item:
                # Update existing item with combined quantity
                existing_qty = duplicate_item['structured'].get('quantity') or 0
                new_qty = parsed.get('quantity') or 0
                duplicate_item['structured']['quantity'] = existing_qty + new_qty

                # Update the item text to reflect new quantity
                duplicate_item['item'] = format_ingredient(duplicate_item['structured'])
                duplicate_item['added'] = today  # Update the date

                logger.info(
                    f"Updated existing item quantity: {duplicate_item['item']}",
                    extra={"recipe": recipe_name, "old_qty": existing_qty, "new_qty": new_qty}
                )
            else:
                # Add new item
                items.append({
                    "item": ing_text,  # Keep original text for reference
                    "structured": parsed,  # Structured parsed data
                    "recipe": recipe_name,
                    "added": today,
                    "checked": False,
                    "category": category
                })
                count += 1

        data["items"] = items

        if _save_list_data(data):
            logger.info(
                "Added items to shopping list",
                extra={"recipe": recipe_name, "count": count}
            )
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to add items to list: {e}", exc_info=True)
        return False


def remove_items_from_list(recipe_name: str, item_names: Optional[List[str]] = None) -> bool:
    """Remove items from the shopping list.

    Args:
        recipe_name: Name of the recipe
        item_names: List of item names to remove. If None, removes all for recipe.

    Returns:
        True if successful, False otherwise
    """
    try:
        data = _load_list_data()
        items = data.get("items", [])

        initial_count = len(items)

        if item_names is None:
            # Remove all for recipe
            items = [i for i in items if i['recipe'] != recipe_name]
        else:
            # Remove specific items for recipe
            # Try matching by both exact item text AND structured ingredient name
            items = [
                i for i in items
                if not (
                    i['recipe'] == recipe_name and (
                        i['item'] in item_names or
                        (i.get('structured', {}).get('name', '') in [
                            name.lower().strip() for name in item_names
                        ])
                    )
                )
            ]

        data["items"] = items

        if _save_list_data(data):
            removed_count = initial_count - len(items)
            logger.info(
                "Removed items from shopping list",
                extra={"recipe": recipe_name, "count": removed_count}
            )
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to remove items from list: {e}", exc_info=True)
        return False


def toggle_item_checked(recipe_name: str, item_name: str, checked: bool) -> bool:
    """Toggle the checked state of an item.

    Args:
        recipe_name: Recipe name
        item_name: Item name (can be original item text or structured name)
        checked: New checked state

    Returns:
        True if successful
    """
    try:
        data = _load_list_data()
        items = data.get("items", [])

        item_name_lower = item_name.lower().strip()

        for item in items:
            # Match by exact item text OR by structured name
            if item['recipe'] == recipe_name and (
                item['item'] == item_name or
                item.get('structured', {}).get('name', '') == item_name_lower
            ):
                item['checked'] = checked

        data["items"] = items
        return _save_list_data(data)

    except Exception as e:
        logger.error(f"Failed to toggle item: {e}", exc_info=True)
        return False


def clear_shopping_list() -> bool:
    """Clear all items from the shopping list.

    Returns:
        True if successful
    """
    try:
        data = {"items": [], "last_updated": datetime.now().isoformat()}
        return _save_list_data(data)
    except Exception as e:
        logger.error(f"Failed to clear list: {e}", exc_info=True)
        return False


def get_combined_shopping_list() -> List[Dict]:
    """Get shopping list with combined quantities using fuzzy matching.

    Combines duplicate ingredients (e.g., "mushrooms" and "mushroom")
    across all recipes.

    Returns:
        List of combined ingredient dictionaries
    """
    try:
        items = load_shopping_list()

        # Extract structured ingredients
        structured_items = [
            item.get('structured')
            for item in items
            if 'structured' in item and item.get('structured')
        ]

        if not structured_items:
            logger.info("No structured items to combine")
            return items

        # Combine using fuzzy matching
        combined = combine_ingredients(structured_items)

        # Add back metadata (category, checked status, etc.)
        result = []
        for combined_ing in combined:
            # Find original items that contributed to this combined ingredient
            ing_name = combined_ing.get("name", "").lower()

            # Find matching original items
            original_items = [
                item for item in items
                if item.get('structured', {}).get('name', '').lower() == ing_name
            ]

            if original_items:
                # Use first item's metadata
                first_item = original_items[0]

                result.append({
                    "item": format_ingredient(combined_ing),
                    "structured": combined_ing,
                    "category": first_item.get('category', 'Other'),
                    "recipes": list(set(item.get('recipe', 'Unknown') for item in original_items)),
                    "recipe_count": len(set(item.get('recipe') for item in original_items)),
                    "checked": any(item.get('checked', False) for item in original_items),
                    "added": max(item.get('added', '') for item in original_items)
                })
            else:
                # Fallback if no match found
                result.append({
                    "item": format_ingredient(combined_ing),
                    "structured": combined_ing,
                    "category": 'Other',
                    "recipes": [],
                    "recipe_count": 1,
                    "checked": False,
                    "added": datetime.now().strftime("%Y-%m-%d")
                })

        logger.info(f"Combined {len(items)} items into {len(result)} items")
        return result

    except Exception as e:
        logger.error(f"Failed to get combined list: {e}", exc_info=True)
        # Fallback to regular list
        return load_shopping_list()


def get_grouped_shopping_list() -> Dict[str, List[Dict]]:
    """Get shopping list grouped by store sections with combined quantities.

    Returns:
        Dictionary mapping category names to lists of combined ingredients
    """
    try:
        combined_items = get_combined_shopping_list()

        # Group by category
        grouped: Dict[str, List[Dict]] = {}

        for item in combined_items:
            category = item.get('category', 'Other')

            if category not in grouped:
                grouped[category] = []

            grouped[category].append(item)

        # Sort categories by importance
        category_order = [
            "Fresh Produce",
            "Dairy & Eggs",
            "Proteins",
            "Grains & Pasta",
            "Canned & Dried",
            "Frozen Foods",
            "Beverages",
            "Baking Supplies",
            "Snacks",
            "Other"
        ]

        # Create ordered result
        result = {}
        for category in category_order:
            if category in grouped:
                result[category] = grouped[category]

        # Add any categories not in the order list
        for category in grouped:
            if category not in result:
                result[category] = grouped[category]

        logger.info(f"Grouped {len(combined_items)} items into {len(result)} categories")
        return result

    except Exception as e:
        logger.error(f"Failed to group shopping list: {e}", exc_info=True)
        # Fallback to ungrouped
        return {"Other": load_shopping_list()}
