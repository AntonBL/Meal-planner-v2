"""Weekly Plan Management Functions.

Shared functions for managing the weekly meal plan using JSON storage.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from lib.constants import RECIPE_SOURCE_GENERATED

from lib.logging_config import get_logger
from lib.recipe_store import get_recipe_by_name, save_recipe

logger = get_logger(__name__)


from lib.shopping_list_manager import add_items_to_list, remove_items_from_list

# ============================================================================
# SHOPPING LIST HELPERS
# ============================================================================

def add_ingredients_to_shopping_list(recipe_name: str, ingredients: str) -> bool:
    """Add ingredients to shopping list when recipe is added to plan.

    Args:
        recipe_name: Name of the recipe
        ingredients: Comma-separated list of ingredients needed

    Returns:
        True if successful, False otherwise
    """
    # Convert comma-separated string to list
    if not ingredients:
        return True
        
    ing_list = [i.strip() for i in ingredients.split(',') if i.strip()]
    return add_items_to_list(recipe_name, ing_list)


def remove_recipe_from_shopping_list(recipe_name: str) -> bool:
    """Remove a recipe's ingredients from shopping list.

    Args:
        recipe_name: Name of the recipe

    Returns:
        True if successful, False otherwise
    """
    return remove_items_from_list(recipe_name)


# ============================================================================
# WEEKLY PLAN MANAGEMENT (JSON)
# ============================================================================

def _get_weekly_plan_path() -> Path:
    """Get the path to the weekly plan JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "weekly_plan.json"


def _load_plan_data() -> dict:
    """Load the full weekly plan data structure from JSON."""
    plan_path = _get_weekly_plan_path()
    if not plan_path.exists():
        return {"current_plan": [], "history": [], "last_updated": None}
    
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse weekly plan JSON: {e}")
        return {"current_plan": [], "history": [], "last_updated": None}


def _save_plan_data(data: dict) -> bool:
    """Save the full weekly plan data structure to JSON."""
    try:
        plan_path = _get_weekly_plan_path()
        data["last_updated"] = datetime.now().isoformat()
        
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save weekly plan JSON: {e}")
        return False





def load_current_plan() -> list[dict]:
    """Load the current weekly meal plan.

    Returns:
        List of meal dictionaries from the current plan
    """

    data = _load_plan_data()
    return data.get("current_plan", [])


def add_recipe_to_plan(recipe: dict) -> bool:
    """Add a recipe to the weekly meal plan.

    Args:
        recipe: Recipe dictionary with name, time, difficulty, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        data = _load_plan_data()
        current_plan = data.get("current_plan", [])

        # Check if plan is full
        if len(current_plan) >= 7:
            logger.warning("Cannot add recipe - plan is full")
            st.warning("⚠️ Your plan is full (7 meals). Remove a meal first.")
            return False

        # Check if recipe already in plan
        if any(meal['name'] == recipe['name'] for meal in current_plan):
            st.info(f"ℹ️ {recipe['name']} is already in your plan")
            return False

        # Build entry
        meal_entry = {
            "name": recipe['name'],
            "recipe_id": recipe.get('id'),
            "source": recipe.get('source', 'Unknown'),
            "time_minutes": recipe.get('time_minutes'),
            "difficulty": recipe.get('difficulty'),
            "added": datetime.now().strftime('%Y-%m-%d')
        }

        current_plan.append(meal_entry)
        data["current_plan"] = current_plan
        
        if _save_plan_data(data):
            logger.info(
                "Added recipe to weekly plan",
                extra={"recipe_name": recipe['name'], "plan_size": len(current_plan)}
            )

            # Clear Streamlit cache if available
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()

            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Failed to add recipe to plan: {e}", exc_info=True)
        return False


def remove_meal_from_plan(index: int) -> bool:
    """Remove a meal from the weekly plan.

    Args:
        index: Index of meal to remove (0-based)

    Returns:
        True if successful, False otherwise
    """
    try:
        data = _load_plan_data()
        current_plan = data.get("current_plan", [])

        if index < 0 or index >= len(current_plan):
            logger.error(f"Invalid index: {index}")
            return False

        # Remove the meal
        removed_meal = current_plan.pop(index)
        data["current_plan"] = current_plan
        
        if _save_plan_data(data):
            logger.info(
                "Removed meal from plan",
                extra={"meal_name": removed_meal['name'], "new_plan_size": len(current_plan)}
            )

            # Remove ingredients from shopping list
            remove_recipe_from_shopping_list(removed_meal['name'])

            # Clear cache
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()

            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Failed to remove meal from plan: {e}", exc_info=True)
        return False


def clear_weekly_plan() -> bool:
    """Clear the entire weekly plan (with archiving to history).

    Returns:
        True if successful, False otherwise
    """
    try:
        data = _load_plan_data()
        current_plan = data.get("current_plan", [])

        if not current_plan:
            st.info("ℹ️ Plan is already empty")
            return True

        # Archive to history
        week_of = datetime.now().strftime("%Y-%m-%d")
        history_entry = {
            "week_of": week_of,
            "meals": current_plan
        }
        
        if "history" not in data:
            data["history"] = []
            
        data["history"].insert(0, history_entry) # Add to beginning
        data["current_plan"] = []
        
        if _save_plan_data(data):
            logger.info("Cleared weekly plan and archived to history")

            # Clear cache
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()

            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Failed to clear weekly plan: {e}", exc_info=True)
        return False
