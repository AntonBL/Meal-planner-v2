"""Shopping List Management Functions.

Shared functions for managing the shopping list using JSON storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from lib.file_manager import get_data_file_path
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


def _migrate_markdown_list_if_needed():
    """Migrate legacy markdown shopping list to JSON if JSON doesn't exist."""
    json_path = _get_shopping_list_path()
    if json_path.exists():
        return

    try:
        # Try to load legacy markdown file
        md_path = get_data_file_path("shopping_list")
        if not md_path.exists():
            return

        logger.info("Migrating shopping list from markdown to JSON...")
        content = md_path.read_text(encoding="utf-8")
        
        lines = content.split('\n')
        items = []
        current_recipe = None
        added_date = datetime.now().strftime("%Y-%m-%d")

        for line in lines:
            line = line.strip()
            
            # Recipe header
            if line.startswith('##'):
                recipe_part = line.replace('##', '').strip()
                if 'For:' in recipe_part:
                    recipe_part = recipe_part.split('For:')[1].strip()
                
                if '(Added:' in recipe_part:
                    parts = recipe_part.split('(Added:')
                    current_recipe = parts[0].strip()
                    added_date = parts[1].replace(')', '').strip()
                else:
                    current_recipe = recipe_part.strip()
                    added_date = datetime.now().strftime("%Y-%m-%d")
            
            # Item line
            elif line.startswith('-') and current_recipe:
                item_text = line[1:].strip()
                if item_text:
                    items.append({
                        "item": item_text,
                        "recipe": current_recipe,
                        "added": added_date,
                        "checked": False,
                        "category": categorize_ingredient(item_text)
                    })

        # Save to JSON
        data = {
            "items": items,
            "last_updated": datetime.now().isoformat()
        }
        _save_list_data(data)
        logger.info(f"Migrated {len(items)} items to shopping_list.json")

    except Exception as e:
        logger.error(f"Failed to migrate shopping list: {e}")


def categorize_ingredient(ingredient_name: str) -> str:
    """Categorize ingredient as 'staple' or 'fresh' based on keywords.

    Args:
        ingredient_name: Name of the ingredient

    Returns:
        'staple' or 'fresh'
    """
    ingredient_lower = ingredient_name.lower()

    # Fresh item keywords
    fresh_keywords = [
        'milk', 'cheese', 'yogurt', 'cream', 'butter',
        'egg', 'eggs',
        'lettuce', 'spinach', 'kale', 'arugula', 'greens',
        'tomato', 'tomatoes', 'cucumber', 'pepper', 'peppers',
        'onion', 'onions', 'garlic', 'ginger',
        'carrot', 'carrots', 'celery', 'broccoli', 'cauliflower',
        'mushroom', 'mushrooms',
        'potato', 'potatoes', 'sweet potato',
        'avocado', 'avocados',
        'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges',
        'lemon', 'lemons', 'lime', 'limes',
        'fresh', 'tofu', 'tempeh'
    ]

    # Check if any fresh keyword is in the ingredient
    for keyword in fresh_keywords:
        if keyword in ingredient_lower:
            return 'fresh'

    # Default to staple
    return 'staple'


def load_shopping_list() -> List[Dict]:
    """Load the current shopping list items.

    Returns:
        List of item dictionaries
    """
    _migrate_markdown_list_if_needed()
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
