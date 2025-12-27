"""Generated Recipes Manager - Persistent storage for generated recipe suggestions.

Manages the generated recipes state across sessions by storing them in a JSON file.
This allows users to close and reopen the recipe generator page without losing suggestions.

Generated recipes auto-expire after a configured timeout to prevent clutter.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from lib.logging_config import get_logger

logger = get_logger(__name__)

# File name for generated recipes
GENERATED_RECIPES_FILE = "generated_recipes.json"

# Auto-cleanup timeout (days)
GENERATED_RECIPES_TIMEOUT_DAYS = 7


def _get_generated_recipes_path() -> Path:
    """Get the path to the generated recipes JSON file.

    Returns:
        Path object pointing to the generated recipes file
    """
    return Path(__file__).parent.parent / "data" / GENERATED_RECIPES_FILE


def save_generated_recipes(recipes: list[dict], params: dict) -> bool:
    """Save generated recipe suggestions to persistent storage.

    Args:
        recipes: List of recipe dictionaries
        params: Generation parameters (cuisines, meal_type, etc.)

    Returns:
        True if successful, False otherwise
    """
    try:
        generated_recipes_path = _get_generated_recipes_path()
        generated_recipes_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "recipes": recipes,
            "generation_params": params,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=GENERATED_RECIPES_TIMEOUT_DAYS)).isoformat()
        }

        with open(generated_recipes_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            "Saved generated recipes to file",
            extra={
                "count": len(recipes),
                "path": str(generated_recipes_path),
                "expires_in_days": GENERATED_RECIPES_TIMEOUT_DAYS
            }
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to save generated recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def load_generated_recipes() -> Optional[dict]:
    """Load generated recipe suggestions from persistent storage.

    Returns:
        Dictionary with 'recipes' and 'generation_params' keys, or None if not found
    """
    try:
        generated_recipes_path = _get_generated_recipes_path()

        if not generated_recipes_path.exists():
            logger.debug("No generated recipes file found")
            return None

        with open(generated_recipes_path, encoding='utf-8') as f:
            data = json.load(f)

        logger.info(
            "Loaded generated recipes from file",
            extra={"count": len(data.get('recipes', []))}
        )

        return data

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse generated recipes JSON",
            extra={"error": str(e)},
            exc_info=True
        )
        return None

    except Exception as e:
        logger.error(
            "Failed to load generated recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return None


def clear_generated_recipes() -> bool:
    """Clear generated recipes from persistent storage.

    Returns:
        True if successful, False otherwise
    """
    try:
        generated_recipes_path = _get_generated_recipes_path()

        if generated_recipes_path.exists():
            generated_recipes_path.unlink()
            logger.info("Cleared generated recipes file")
        else:
            logger.debug("No generated recipes file to clear")

        return True

    except Exception as e:
        logger.error(
            "Failed to clear generated recipes",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def has_generated_recipes() -> bool:
    """Check if there are generated recipes saved.

    Returns:
        True if generated recipes exist, False otherwise
    """
    try:
        generated_recipes_path = _get_generated_recipes_path()
        return generated_recipes_path.exists()
    except Exception:
        return False


def are_generated_recipes_expired() -> bool:
    """Check if generated recipes have expired.

    Returns:
        True if recipes exist and are expired, False otherwise
    """
    try:
        data = load_generated_recipes()
        if not data:
            return False

        expires_at_str = data.get('expires_at')
        if not expires_at_str:
            # No expiration date means old format - consider expired
            logger.info("Generated recipes have no expiration date (old format)")
            return True

        expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now()

        is_expired = now > expires_at
        if is_expired:
            logger.info(
                "Generated recipes have expired",
                extra={
                    "expired_at": expires_at_str,
                    "current_time": now.isoformat()
                }
            )

        return is_expired

    except Exception as e:
        logger.error(
            "Failed to check recipe expiration",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


def get_generated_recipes_age() -> Optional[int]:
    """Get the age of generated recipes in days.

    Returns:
        Age in days, or None if no recipes exist
    """
    try:
        data = load_generated_recipes()
        if not data:
            return None

        created_at_str = data.get('created_at')
        if not created_at_str:
            return None

        created_at = datetime.fromisoformat(created_at_str)
        age = (datetime.now() - created_at).days

        return age

    except Exception as e:
        logger.error(
            "Failed to get recipe age",
            extra={"error": str(e)},
            exc_info=True
        )
        return None
