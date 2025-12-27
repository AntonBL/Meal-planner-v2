"""Active Recipe Manager - Persistent storage for currently cooking recipe(s).

Manages the active recipe state across sessions by storing it in a JSON file.
Supports both single-recipe and multi-recipe cooking sessions.
"""

import json
from pathlib import Path
from typing import Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)

# File name for active recipes (changed to support multiple)
ACTIVE_RECIPES_FILE = "active_recipes.json"
# Legacy file for backward compatibility
ACTIVE_RECIPE_FILE = "active_recipe.json"


def _get_active_recipe_path() -> Path:
    """Get the path to the active recipe JSON file.

    Returns:
        Path object pointing to the active recipe file
    """
    return Path(__file__).parent.parent / "data" / ACTIVE_RECIPE_FILE


def save_active_recipe(recipe: dict) -> bool:
    """Save the currently active recipe to persistent storage.

    Args:
        recipe: Recipe dictionary with name, ingredients, instructions, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the active recipe path
        active_recipe_path = _get_active_recipe_path()
        active_recipe_path.parent.mkdir(parents=True, exist_ok=True)

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
        # Get the active recipe path
        active_recipe_path = _get_active_recipe_path()

        # Check if file exists
        if not active_recipe_path.exists():
            logger.debug("No active recipe file found")
            return None

        # Read and parse JSON
        with open(active_recipe_path, encoding='utf-8') as f:
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
        # Get the active recipe path
        active_recipe_path = _get_active_recipe_path()

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
        active_recipe_path = _get_active_recipe_path()
        return active_recipe_path.exists()
    except Exception:
        return False


# ============================================================================
# MULTI-RECIPE SUPPORT (New API)
# ============================================================================

def _get_active_recipes_path() -> Path:
    """Get the path to the active recipes JSON file (multi-recipe mode).

    Returns:
        Path object pointing to the active recipes file
    """
    return Path(__file__).parent.parent / "data" / ACTIVE_RECIPES_FILE


def save_active_recipes(recipes: list[dict]) -> bool:
    """Save multiple active recipes to persistent storage.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure each recipe has an ID for tracking
        for recipe in recipes:
            if not recipe.get('id'):
                logger.warning(
                    "Recipe missing ID, using name as fallback",
                    extra={"recipe_name": recipe.get('name')}
                )
                # Use name as ID if missing (not ideal, but fallback)
                recipe['id'] = recipe.get('name', 'unknown')

        # Get the active recipes path
        active_recipes_path = _get_active_recipes_path()
        active_recipes_path.parent.mkdir(parents=True, exist_ok=True)

        # Write recipes as JSON array
        with open(active_recipes_path, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)

        logger.info(
            "Saved active recipes to file",
            extra={
                "recipe_count": len(recipes),
                "recipe_names": [r.get('name') for r in recipes],
                "path": str(active_recipes_path)
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to save active recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def load_active_recipes() -> list[dict]:
    """Load all active recipes from persistent storage.

    Returns:
        List of recipe dictionaries, empty list if none found
    """
    try:
        # Get the active recipes path
        active_recipes_path = _get_active_recipes_path()

        # Check if file exists
        if not active_recipes_path.exists():
            logger.debug("No active recipes file found")
            return []

        # Read and parse JSON
        with open(active_recipes_path, encoding='utf-8') as f:
            recipes = json.load(f)

        # Ensure it's a list
        if not isinstance(recipes, list):
            logger.warning("Active recipes file is not a list, returning empty")
            return []

        logger.info(
            "Loaded active recipes from file",
            extra={
                "recipe_count": len(recipes),
                "recipe_names": [r.get('name') for r in recipes]
            }
        )

        return recipes

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse active recipes JSON",
            extra={"error": str(e)},
            exc_info=True
        )
        return []

    except Exception as e:
        logger.error(
            "Failed to load active recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return []


def add_active_recipe(recipe: dict) -> bool:
    """Add a recipe to the active recipes list.

    Args:
        recipe: Recipe dictionary to add

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing recipes
        recipes = load_active_recipes()

        # Check if recipe already active (by ID or name)
        recipe_id = recipe.get('id')
        recipe_name = recipe.get('name')

        for existing in recipes:
            if (recipe_id and existing.get('id') == recipe_id) or \
               (recipe_name and existing.get('name') == recipe_name):
                logger.info(
                    "Recipe already in active list",
                    extra={"recipe_name": recipe_name}
                )
                return True  # Not an error, just already there

        # Add new recipe
        recipes.append(recipe)

        # Save updated list
        return save_active_recipes(recipes)

    except Exception as e:
        logger.error(
            "Failed to add active recipe",
            extra={"recipe_name": recipe.get('name'), "error": str(e)},
            exc_info=True
        )
        return False


def remove_active_recipe(recipe_id: str) -> bool:
    """Remove a recipe from the active recipes list.

    Args:
        recipe_id: ID or name of the recipe to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing recipes
        recipes = load_active_recipes()

        # Filter out the recipe by ID or name
        initial_count = len(recipes)
        recipes = [
            r for r in recipes
            if r.get('id') != recipe_id and r.get('name') != recipe_id
        ]

        if len(recipes) == initial_count:
            logger.warning(
                "Recipe not found in active list",
                extra={"recipe_id": recipe_id}
            )
            return False

        # Save updated list
        return save_active_recipes(recipes)

    except Exception as e:
        logger.error(
            "Failed to remove active recipe",
            extra={"recipe_id": recipe_id, "error": str(e)},
            exc_info=True
        )
        return False


def clear_active_recipes() -> bool:
    """Clear all active recipes from persistent storage.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the active recipes path
        active_recipes_path = _get_active_recipes_path()

        # Remove file if it exists
        if active_recipes_path.exists():
            active_recipes_path.unlink()
            logger.info("Cleared active recipes file")
        else:
            logger.debug("No active recipes file to clear")

        return True

    except Exception as e:
        logger.error(
            "Failed to clear active recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def has_active_recipes() -> bool:
    """Check if there are any active recipes saved.

    Returns:
        True if active recipes exist, False otherwise
    """
    try:
        active_recipes_path = _get_active_recipes_path()
        if not active_recipes_path.exists():
            return False

        recipes = load_active_recipes()
        return len(recipes) > 0

    except Exception:
        return False
