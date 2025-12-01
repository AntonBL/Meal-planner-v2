"""Meal History Management Functions.

Shared functions for managing meal history using JSON storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


from lib.logging_config import get_logger

logger = get_logger(__name__)


def _get_history_path() -> Path:
    """Get the path to the meal history JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "meal_history.json"


def _load_history_data() -> dict:
    """Load the full meal history data structure from JSON."""
    history_path = _get_history_path()
    if not history_path.exists():
        return {"meals": [], "last_updated": None}
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse meal history JSON: {e}")
        return {"meals": [], "last_updated": None}


def _save_history_data(data: dict) -> bool:
    """Save the full meal history data structure to JSON."""
    try:
        history_path = _get_history_path()
        data["last_updated"] = datetime.now().isoformat()
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save meal history JSON: {e}")
        return False


        # Save to JSON
        data = {
            "meals": meals,
            "last_updated": datetime.now().isoformat()
        }
        _save_history_data(data)
        logger.info(f"Migrated {len(meals)} meals to meal_history.json")

    except Exception as e:
        logger.error(f"Failed to migrate meal history: {e}", exc_info=True)


def load_meal_history() -> List[Dict]:
    """Load all meal history.

    Returns:
        List of meal dictionaries
    """

    data = _load_history_data()
    return data.get("meals", [])


def add_meal_to_history(meal_data: dict) -> bool:
    """Add a meal to history.

    Args:
        meal_data: Dictionary with date, name, rating, notes, ingredients

    Returns:
        True if successful
    """
    try:
        data = _load_history_data()
        meals = data.get("meals", [])
        
        # Ensure date
        if "date" not in meal_data:
            meal_data["date"] = datetime.now().strftime("%A, %Y-%m-%d")
            
        # Insert at beginning (newest first)
        meals.insert(0, meal_data)
        data["meals"] = meals
        
        if _save_history_data(data):
            logger.info(f"Added meal to history: {meal_data.get('name')}")
            return True
        return False

    except Exception as e:
        logger.error(f"Failed to add meal to history: {e}", exc_info=True)
        return False
