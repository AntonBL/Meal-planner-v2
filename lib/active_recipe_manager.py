"""Active Recipe Manager - Persistent storage for currently cooking recipe.

Manages the active recipe state across sessions by storing it in a JSON file.
"""

import json
from pathlib import Path
from typing import Optional

from lib.file_manager import get_data_file_path
from lib.logging_config import get_logger

logger = get_logger(__name__)

# File path for active recipe
ACTIVE_RECIPE_FILE = "active_recipe.json"


def save_active_recipe(recipe: dict) -> bool:
    """Save the currently active recipe to persistent storage.

    Args:
        recipe: Recipe dictionary with name, ingredients, instructions, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the data directory path
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        active_recipe_path = data_dir / ACTIVE_RECIPE_FILE

        # Write recipe as JSON for easy parsing
        with open(active_recipe_path, 'w', encoding='utf-8') as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)

        logger.info(
            "Saved active recipe to file",
            extra={"recipe_name": recipe.get('name'), "path": str(active_recipe_path)}
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to save active recipe",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False


def load_active_recipe() -> Optional[dict]:
    """Load the currently active recipe from persistent storage.

    Returns:
        Recipe dictionary if found, None otherwise
    """
    try:
        # Get the data directory path
        data_dir = Path(__file__).parent.parent / "data"
        active_recipe_path = data_dir / ACTIVE_RECIPE_FILE

        # Check if file exists
        if not active_recipe_path.exists():
            logger.debug("No active recipe file found")
            return None

        # Read and parse JSON
        with open(active_recipe_path, 'r', encoding='utf-8') as f:
            recipe = json.load(f)

        logger.info(
            "Loaded active recipe from file",
            extra={"recipe_name": recipe.get('name')}
        )

        return recipe

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse active recipe JSON",
            extra={"error": str(e)},
            exc_info=True
        )
        return None

    except Exception as e:
        logger.error(
            "Failed to load active recipe",
            extra={"error": str(e)},
            exc_info=True
        )
        return None


def clear_active_recipe() -> bool:
    """Clear the active recipe from persistent storage.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the data directory path
        data_dir = Path(__file__).parent.parent / "data"
        active_recipe_path = data_dir / ACTIVE_RECIPE_FILE

        # Remove file if it exists
        if active_recipe_path.exists():
            active_recipe_path.unlink()
            logger.info("Cleared active recipe file")
        else:
            logger.debug("No active recipe file to clear")

        return True

    except Exception as e:
        logger.error(
            "Failed to clear active recipe",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def has_active_recipe() -> bool:
    """Check if there's an active recipe saved.

    Returns:
        True if active recipe exists, False otherwise
    """
    try:
        data_dir = Path(__file__).parent.parent / "data"
        active_recipe_path = data_dir / ACTIVE_RECIPE_FILE
        return active_recipe_path.exists()

    except Exception:
        return False
