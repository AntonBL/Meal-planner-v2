"""File operations and Context Loading.

This module now serves as an adapter to load data from JSON stores
and format it for LLM context generation.
"""

import logging
from pathlib import Path
from typing import Literal

from lib.exceptions import DataFileNotFoundError
from lib.history_manager import load_meal_history
from lib.pantry_manager import load_pantry_items
from lib.recipe_store import load_recipes
from lib.shopping_list_manager import load_shopping_list

logger = logging.getLogger(__name__)

# Type alias for valid data file types (Legacy support mostly)
DataFileType = Literal[
    "staples",
    "fresh",
    "shopping_list",
    "loved_recipes",
    "liked_recipes",
    "not_again_recipes",
    "generated_recipes",
    "preferences",
    "meal_history",
    "weekly_plan",
]


def get_data_file_path(file_type: DataFileType) -> Path:
    """Get the path to a data file by type.
    
    Kept for legacy support during transition, but most data is now in JSON.
    """
    file_map = {
        "staples": "data/pantry/staples.md",
        "fresh": "data/pantry/fresh.md",
        "shopping_list": "data/pantry/shopping_list.md",
        "loved_recipes": "data/recipes/loved.md",
        "liked_recipes": "data/recipes/liked.md",
        "not_again_recipes": "data/recipes/not_again.md",
        "generated_recipes": "data/recipes/generated.md",
        "preferences": "data/preferences.md",
        "meal_history": "data/meal_history.md",
        "weekly_plan": "data/weekly_plan.md",
    }

    if file_type not in file_map:
        raise ValueError(f"Unknown file type: {file_type}")

    return Path(file_map[file_type])


def load_context_for_recipe_generation() -> dict[str, str]:
    """Load all data needed for recipe generation from JSON stores.

    Returns:
        Dictionary containing formatted strings for:
        - staples, fresh (pantry items)
        - shopping_list
        - loved_recipes, preferences, meal_history
    """
    logger.info("Loading context for recipe generation from JSON")

    try:
        # 1. Load Pantry
        pantry_items = load_pantry_items()
        staples = [f"- {i['name']}" for i in pantry_items if i.get('type') == 'staple']
        fresh = [f"- {i['name']} (Qty: {i.get('quantity', '?')})" for i in pantry_items if i.get('type') == 'fresh']

        # 2. Load Shopping List
        shopping_items = load_shopping_list()
        shopping_list = [f"- {i['item']} (for {i.get('recipe', 'unknown')})" for i in shopping_items if not i.get('checked')]

        # 3. Load Recipes (for loved/liked)
        all_recipes = load_recipes()
        loved = [f"- {r['name']}" for r in all_recipes if r.get('rating', 0) == 5]
        
        # 4. Load Meal History
        history = load_meal_history()
        # Format last 10 meals
        recent_meals = [
            f"- {m['date']}: {m['name']} (Rating: {m.get('rating', '?')}/5)"
            for m in history[:10]
        ]

        # 5. Load Preferences (Legacy file or default)
        # We might still want to keep preferences.md or move it to JSON.
        # For now, let's try to read it if it exists, otherwise return empty.
        preferences = ""
        pref_path = Path("data/preferences.md")
        if pref_path.exists():
            preferences = pref_path.read_text(encoding="utf-8")

        context = {
            "staples": "\n".join(staples) if staples else "None",
            "fresh": "\n".join(fresh) if fresh else "None",
            "shopping_list": "\n".join(shopping_list) if shopping_list else "None",
            "loved_recipes": "\n".join(loved) if loved else "None",
            "meal_history": "\n".join(recent_meals) if recent_meals else "None",
            "preferences": preferences,
        }

        logger.info("Recipe generation context loaded successfully")
        return context

    except Exception as e:
        logger.error(f"Failed to load recipe generation context: {e}", exc_info=True)
        # Return empty context rather than crashing, to allow partial functionality
        return {
            "staples": "", "fresh": "", "shopping_list": "",
            "loved_recipes": "", "meal_history": "", "preferences": ""
        }
