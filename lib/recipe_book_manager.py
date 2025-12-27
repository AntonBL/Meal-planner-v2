"""Recipe Book Manager - Curated recipe collection management with JSON storage.

This module provides a separate curated collection of favorite recipes,
distinct from the main recipe working set (recipes.json).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# RECIPE BOOK MANAGER
# ============================================================================


def _get_recipe_book_path() -> Path:
    """Get the path to the recipe book JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "recipe_book.json"


def load_recipe_book() -> list[dict]:
    """Load all recipes from the recipe book.

    Returns:
        List of recipe dictionaries from the curated collection
    """
    try:
        recipe_book_path = _get_recipe_book_path()

        if not recipe_book_path.exists():
            logger.info("Recipe book file doesn't exist, returning empty list")
            return []

        with open(recipe_book_path, encoding='utf-8') as f:
            data = json.load(f)

        recipes = data.get('recipes', [])
        logger.info(f"Loaded {len(recipes)} recipes from recipe book")
        return recipes

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse recipe book JSON: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Failed to load recipe book: {e}", exc_info=True)
        return []


def save_recipe_book(recipes: list[dict]) -> bool:
    """Save all recipes to the recipe book.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        True if successful, False otherwise
    """
    try:
        recipe_book_path = _get_recipe_book_path()
        recipe_book_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'last_updated': datetime.now().isoformat(),
            'recipes': recipes
        }

        with open(recipe_book_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(recipes)} recipes to recipe book")
        return True

    except Exception as e:
        logger.error(f"Failed to save recipe book: {e}", exc_info=True)
        return False


def get_recipe_book_recipe_by_id(recipe_id: str) -> Optional[dict]:
    """Get a single recipe from the book by its ID.

    Args:
        recipe_id: UUID of the recipe

    Returns:
        Recipe dictionary or None if not found
    """
    recipes = load_recipe_book()
    for recipe in recipes:
        if recipe.get('id') == recipe_id:
            return recipe

    logger.debug(f"Recipe not found in book: {recipe_id}")
    return None


def is_in_recipe_book(recipe_id: str) -> bool:
    """Check if a recipe exists in the recipe book.

    Args:
        recipe_id: UUID of the recipe

    Returns:
        True if recipe is in the book, False otherwise
    """
    if not recipe_id:
        return False

    return get_recipe_book_recipe_by_id(recipe_id) is not None


def add_to_recipe_book(recipe: dict) -> bool:
    """Add a recipe to the curated recipe book.

    Adds a timestamp tracking when the recipe was added to the book.
    Prevents duplicate additions.

    Args:
        recipe: Recipe dictionary to add

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes = load_recipe_book()

        # Check for duplicates
        recipe_id = recipe.get('id')
        if not recipe_id:
            logger.error("Cannot add recipe without ID to book")
            return False

        if is_in_recipe_book(recipe_id):
            logger.warning(f"Recipe already in book: {recipe.get('name')}")
            return False

        # Add timestamp
        recipe_copy = recipe.copy()
        recipe_copy['added_to_book'] = datetime.now().isoformat()

        recipes.append(recipe_copy)
        logger.info(f"Added recipe to book: {recipe.get('name')}")

        return save_recipe_book(recipes)

    except Exception as e:
        logger.error(f"Failed to add recipe to book: {e}", exc_info=True)
        return False


def remove_from_recipe_book(recipe_id: str) -> bool:
    """Remove a recipe from the recipe book.

    Note: This only removes the recipe from the curated collection,
    it does not delete the recipe from the main recipe store.

    Args:
        recipe_id: UUID of the recipe to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes = load_recipe_book()
        original_count = len(recipes)

        recipes = [r for r in recipes if r.get('id') != recipe_id]

        if len(recipes) == original_count:
            logger.warning(f"Recipe not found in book for removal: {recipe_id}")
            return False

        logger.info(f"Removed recipe from book: {recipe_id}")
        return save_recipe_book(recipes)

    except Exception as e:
        logger.error(f"Failed to remove recipe from book: {e}", exc_info=True)
        return False


def update_recipe_book_recipe(recipe: dict) -> bool:
    """Update an existing recipe in the recipe book.

    Args:
        recipe: Recipe dictionary with updated fields

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes = load_recipe_book()

        recipe_id = recipe.get('id')
        if not recipe_id:
            logger.error("Cannot update recipe without ID")
            return False

        # Find and update the recipe
        found = False
        for i, r in enumerate(recipes):
            if r.get('id') == recipe_id:
                # Preserve added_to_book timestamp
                if 'added_to_book' in r and 'added_to_book' not in recipe:
                    recipe['added_to_book'] = r['added_to_book']

                recipes[i] = recipe
                found = True
                logger.info(f"Updated recipe in book: {recipe.get('name')}")
                break

        if not found:
            logger.warning(f"Recipe not found in book for update: {recipe_id}")
            return False

        return save_recipe_book(recipes)

    except Exception as e:
        logger.error(f"Failed to update recipe in book: {e}", exc_info=True)
        return False
