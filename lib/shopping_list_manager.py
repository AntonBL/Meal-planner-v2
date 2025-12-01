"""Shopping List Management Functions.

Shared functions for managing the shopping list using JSON storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


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


def load_shopping_list() -> List[Dict]:
    """Load the current shopping list items.

    Returns:
        List of item dictionaries
    """

    data = _load_list_data()
    return data.get("items", [])


def add_items_to_list(recipe_name: str, ingredients: List[str]) -> bool:
    """Add ingredients for a recipe to the shopping list.

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

        count = 0
        for ing in ingredients:
            ing = ing.strip()
            if not ing:
                continue
                
            # Check for duplicates (same item for same recipe)
            if not any(i['item'] == ing and i['recipe'] == recipe_name for i in items):
                items.append({
                    "item": ing,
                    "recipe": recipe_name,
                    "added": today,
                    "checked": False,
                    "category": categorize_ingredient(ing)
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
            items = [
                i for i in items 
                if not (i['recipe'] == recipe_name and i['item'] in item_names)
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
        item_name: Item name
        checked: New checked state

    Returns:
        True if successful
    """
    try:
        data = _load_list_data()
        items = data.get("items", [])
        
        for item in items:
            if item['recipe'] == recipe_name and item['item'] == item_name:
                item['checked'] = checked
                break
                
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
