"""Recipe Store - Central recipe management with JSON storage.

This module provides a centralized recipe store using JSON for fast,
reliable access to recipe data. Replaces the fragmented markdown-based
storage system.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# RECIPE STORE
# ============================================================================


def _get_recipes_path() -> Path:
    """Get the path to the recipes JSON file."""
    # Use direct path construction instead of get_data_file_path
    # since "recipes" is not a registered file type
    data_dir = Path(__file__).parent.parent / "data"
    return data_dir / "recipes.json"


def load_recipes() -> list[dict]:
    """Load all recipes from JSON storage.

    Returns:
        List of recipe dictionaries
    """
    try:
        recipes_path = _get_recipes_path()

        if not recipes_path.exists():
            logger.info("Recipes file doesn't exist, returning empty list")
            return []

        with open(recipes_path, encoding='utf-8') as f:
            data = json.load(f)

        recipes = data.get('recipes', [])
        logger.info(f"Loaded {len(recipes)} recipes from JSON")
        return recipes

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse recipes JSON: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Failed to load recipes: {e}", exc_info=True)
        return []


def save_recipes(recipes: list[dict]) -> bool:
    """Save all recipes to JSON storage.

    Args:
        recipes: List of recipe dictionaries

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes_path = _get_recipes_path()
        recipes_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'last_updated': datetime.now().isoformat(),
            'recipes': recipes
        }

        with open(recipes_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(recipes)} recipes to JSON")
        return True

    except Exception as e:
        logger.error(f"Failed to save recipes: {e}", exc_info=True)
        return False


def get_recipe_by_id(recipe_id: str) -> Optional[dict]:
    """Get a single recipe by its ID.

    Args:
        recipe_id: UUID of the recipe

    Returns:
        Recipe dictionary or None if not found
    """
    recipes = load_recipes()
    for recipe in recipes:
        if recipe.get('id') == recipe_id:
            return recipe

    logger.warning(f"Recipe not found: {recipe_id}")
    return None


def get_recipe_by_name(name: str) -> Optional[dict]:
    """Get a recipe by its name (case-insensitive).

    Args:
        name: Recipe name

    Returns:
        Recipe dictionary or None if not found
    """
    recipes = load_recipes()
    for recipe in recipes:
        if recipe.get('name', '').lower() == name.lower():
            return recipe

    logger.debug(f"Recipe not found by name: {name}")
    return None


def save_recipe(recipe: dict) -> bool:
    """Save or update a single recipe.

    If the recipe has an 'id', it will update the existing recipe.
    Otherwise, it will create a new recipe with a generated ID.

    Args:
        recipe: Recipe dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes = load_recipes()

        # Generate ID if not present
        if 'id' not in recipe:
            recipe['id'] = str(uuid.uuid4())
            recipe['created_date'] = datetime.now().isoformat()
            logger.info(f"Generated new recipe ID: {recipe['id']}")

        # Update existing or append new
        existing_index = None
        for i, r in enumerate(recipes):
            if r.get('id') == recipe['id']:
                existing_index = i
                break

        if existing_index is not None:
            recipes[existing_index] = recipe
            logger.info(f"Updated recipe: {recipe.get('name')}")
        else:
            recipes.append(recipe)
            logger.info(f"Added new recipe: {recipe.get('name')}")

        return save_recipes(recipes)

    except Exception as e:
        logger.error(f"Failed to save recipe: {e}", exc_info=True)
        return False


def delete_recipe(recipe_id: str) -> bool:
    """Delete a recipe by its ID.

    Args:
        recipe_id: UUID of the recipe to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        recipes = load_recipes()
        original_count = len(recipes)

        recipes = [r for r in recipes if r.get('id') != recipe_id]

        if len(recipes) == original_count:
            logger.warning(f"Recipe not found for deletion: {recipe_id}")
            return False

        logger.info(f"Deleted recipe: {recipe_id}")
        return save_recipes(recipes)

    except Exception as e:
        logger.error(f"Failed to delete recipe: {e}", exc_info=True)
        return False


def search_recipes(
    source: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_time: Optional[int] = None,
    tags: Optional[list[str]] = None,
    query: Optional[str] = None
) -> list[dict]:
    """Search recipes with filters.

    Args:
        source: Filter by source (Generated, Loved, Liked)
        min_rating: Minimum rating (1-5)
        max_time: Maximum cooking time in minutes
        tags: List of tags to filter by
        query: Search query for name/description

    Returns:
        List of matching recipes
    """
    recipes = load_recipes()
    results = recipes

    if source:
        results = [r for r in results if r.get('source') == source]

    if min_rating is not None:
        results = [r for r in results if r.get('rating', 0) >= min_rating]

    if max_time is not None:
        results = [r for r in results if r.get('time_minutes', 999) <= max_time]

    if tags:
        results = [
            r for r in results
            if any(tag in r.get('tags', []) for tag in tags)
        ]

    if query:
        query_lower = query.lower()
        results = [
            r for r in results
            if query_lower in r.get('name', '').lower()
            or query_lower in r.get('description', '').lower()
        ]

    logger.debug(f"Search returned {len(results)} recipes")
    return results


def update_recipe_stats(recipe_id: str, cooked: bool = True) -> bool:
    """Update recipe statistics after cooking.

    Args:
        recipe_id: UUID of the recipe
        cooked: Whether the recipe was cooked (updates cook_count and last_cooked)

    Returns:
        True if successful, False otherwise
    """
    try:
        recipe = get_recipe_by_id(recipe_id)
        if not recipe:
            return False

        if cooked:
            recipe['cook_count'] = recipe.get('cook_count', 0) + 1
            recipe['last_cooked'] = datetime.now().isoformat()

        return save_recipe(recipe)

    except Exception as e:
        logger.error(f"Failed to update recipe stats: {e}", exc_info=True)
        return False
